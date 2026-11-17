from bcrypt import checkpw, hashpw, gensalt
import os
import httpx
import logging
from datetime import datetime, timezone
from models import UserModel
from repositories.user_repository import UserRepository
from services.mailing_service import EmailService
from schemas.user import UserCreate, UserTypeEnum, UserResponse, CreateUserWithPassword
import jwt
import datetime as dt
from uuid import uuid4
import secrets
import string
import asyncio

logger = logging.getLogger(__name__)

class AuthService:
    def __init__(self, userRepository: UserRepository, mailing_service: EmailService):
        self._userRepository = userRepository
        self._google_client_id = os.getenv("GOOGLE_CLIENT_ID")
        self._secret_key = os.getenv("JWT_SECRET_KEY")
        self._mailing_service = mailing_service

        if not self._secret_key:
            raise ValueError("JWT_SECRET_KEY environment variable is required but not set")
        
    def _generate_otp(self) -> str:
        """
        Generate a one-time password (OTP) for the user.
        
        Returns:
            str: A 6-digit OTP string
        """

        length = 6
        characters = string.digits
        return ''.join(secrets.choice(characters) for _ in range(length))
    
    def _get_active_enrollments(self, user: UserModel) -> list:
        """
        Filter and return only active (non-expired, purchase completed) enrollments.
        
        Args:
            user: User model instance with enrollments loaded
        
        Returns:
            list: List of active enrollment objects
        """
        if not user.enrollments:
            return []
        
        now = datetime.now(timezone.utc)
        return [
            enrollment for enrollment in user.enrollments
            if enrollment.purchase_completed and (
                enrollment.expires_at is None or enrollment.expires_at > now
            )
        ]
        

    def _verify_google_token(self, token: str) -> dict:
        """
        Verify the Google ID token and return the user information.
        
        Args:
            token: Google ID token from OAuth flow
        
        Returns:
            dict: User information dictionary if valid, None otherwise
        """

        try:
            with httpx.Client() as client:
                response = client.get(
                    "https://www.googleapis.com/oauth2/v3/userinfo",
                    headers={"Authorization": f"Bearer {token}"}
                )

                if response.status_code == 200:
                    return response.json()
                
            return None
        except:
            return None


    def _generate_tokens(self, user: UserModel) -> tuple:
        """
        Generate access and refresh tokens for the user.
        
        Args:
            user: User model instance
        
        Returns:
            tuple: (access_token, refresh_token) pair
        """
        access_token = jwt.encode({"sub": str(user.Id), "email": user.email, "exp": dt.datetime.now(dt.timezone.utc) + dt.timedelta(minutes=15)}, self._secret_key, algorithm="HS256")
        refresh_token = str(uuid4())

        return access_token, refresh_token

    def login_with_google(self, token: str) -> dict:
        """
        Log in a user with their Google account using the provided token.
        
        Args:
            token: Google ID token from OAuth flow
        
        Returns:
            dict: Response dictionary with success status, user data, and tokens
        """
        try:
            user_info = self._verify_google_token(token)
            if not user_info:
                return {"success": False, "message": "Invalid token", "status_code": 401}

            email = user_info.get("email")

            user = self._userRepository.get_by_email(email)
            if not user:
                return {"success": False, "message": "User not found! Create account first", "status_code": 404}
            
            if not user.is_active:
                return {"success": False, "message": "User account is disabled", "status_code": 403}

            if user.password_hash:
                return {"success": False, "message": "You have a password set. Please log in with email and password.", "status_code": 400}

            access_token, refresh_token = self._generate_tokens(user)
            # TODO: Limit number of refresh tokens per user
            self._userRepository.save_refresh_token(refresh_token, user.Id)

            # Filter to only include active enrollments in response
            user_data = UserResponse.model_validate(user).model_dump()
            user_data['enrollments'] = [
                enrollment for enrollment in (user_data.get('enrollments') or [])
                if enrollment.get('purchase_completed') and (
                    enrollment.get('expires_at') is None or enrollment.get('expires_at') > datetime.now(timezone.utc)
                )
            ]

            return {
                "success": True,
                "status_code": 200,
                "message": "Login successful",
                "data": user_data,
                "access_token": access_token,
                "refresh_token": refresh_token
            }
        except Exception as e:
            logger.error(f"Google login failed: {str(e)}", exc_info=True)
            return {
                "success": False, 
                "message": "An error occurred while processing your request",
                "status_code": 500
            }

    async def signup_with_google(self, token: str) -> dict:
        """
        Sign up a new user with their Google account using the provided token.
        
        Args:
            token: Google ID token from OAuth flow
        
        Returns:
            dict: Response dictionary with success status, user data, and tokens
        """
        try:
            user_info = self._verify_google_token(token)
            if not user_info:
                return {"success": False, "message": "Invalid token", "status_code": 401}

            email = user_info.get("email")

            user = self._userRepository.get_by_email(email)
            if user:
                return {"success": False, "message": "User already exists", "status_code": 409}

            # Create UserCreate schema instead of UserModel directly
            user_data = UserCreate(
                email=email,
                first_name=user_info.get("given_name").title(),
                last_name=user_info.get("family_name").title(),
                user_type=UserTypeEnum.LEARNER,
                account_verified=True
            )
            user = self._userRepository.create(user_data)

            access_token, refresh_token = self._generate_tokens(user)

            self._userRepository.save_refresh_token(refresh_token, user.Id)

            user_data = UserResponse.model_validate(user).model_dump()

            asyncio.create_task(
                self._mailing_service.send_welcome_email(user.email, user.first_name or "User")
            )

            return {
                "success": True,
                "message": "Sign up successful",
                "status_code": 201,
                "data": user_data,
                "access_token": access_token,
                "refresh_token": refresh_token
            }
        except Exception as e:
            logger.error(f"Google signup failed: {str(e)}", exc_info=True)
            return {
                "success": False, 
                "message": "An error occurred while processing your request",
                "status_code": 500
            }
        
    
    async def email_password_signup(self, user_data: CreateUserWithPassword):
        """
        Sign up a new user with email and password.
        
        Args:
            user_data: User registration data including email and password
        
        Returns:
            dict: Response dictionary with success status, user data, and tokens
        """

        try:
            user = self._userRepository.get_by_email(user_data.email)
            if user:
                return {"success": False, "message": "User already exists", "status_code": 409}
            
            new_user = self._userRepository.create_user_with_password(user_data)
            otp = self._generate_otp()

            asyncio.create_task(
                self._mailing_service.send_otp_email(
                    new_user.email, 
                    otp, 
                    new_user.first_name or "User"
                )
            )

            self._userRepository.create_otp(
                new_user.Id, 
                hashpw(
                    otp.encode("utf-8"), 
                    gensalt()
                ).decode("utf-8"),
            )

            access_token, refresh_token = self._generate_tokens(new_user)

            self._userRepository.save_refresh_token(refresh_token, new_user.Id)

            user_data = UserResponse.model_validate(new_user).model_dump()

            return {
                "success": True,
                "message": "Sign up successful. Verification email will be sent shortly.",
                "status_code": 201,
                "data": user_data,
                "access_token": access_token,
                "refresh_token": refresh_token
            }
        except Exception as e:
            logger.error(f"Email/password signup failed: {str(e)}", exc_info=True)
            return {
                "success": False, 
                "message": "An error occurred while processing your request",
                "status_code": 500
            }

        
    async def email_password_login(self, email: str, password: str) -> dict:
        """
        Log in a user with email and password.
        
        Args:
            email: User's email address
            password: User's password in plain text
        
        Returns:
            dict: Response dictionary with success status, user data, and tokens
        """

        try:
            user = self._userRepository.get_by_email(email)
            if not user:
                return {"success": False, "message": "User not found", "status_code": 404}
            
            if not user.password_hash:
                return {"success": False, "message": "User does not have a password set. Please log in with Google.", "status_code": 400}

            # Verify the password
            if not checkpw(password.encode("utf-8"), user.password_hash.encode("utf-8")):
                return {"success": False, "message": "Invalid password", "status_code": 401}
            
            if not user.account_verified:
                otp = self._generate_otp()
                asyncio.create_task(
                    self._mailing_service.send_otp_email(
                        user.email, 
                        otp, 
                        user.first_name or "User"
                    )
                )

                self._userRepository.create_otp(
                    user.Id, 
                    hashpw(
                        otp.encode("utf-8"), 
                        gensalt()
                    ).decode("utf-8")
                )

            access_token, refresh_token = self._generate_tokens(user)

            self._userRepository.save_refresh_token(refresh_token, user.Id)
            self._userRepository.delete_expired_user_otps(user.Id)

            # Filter to only include active enrollments in response
            user_dict = UserResponse.model_validate(user).model_dump()
            user_dict['enrollments'] = [
                enrollment for enrollment in (user_dict.get('enrollments') or [])
                if enrollment.get('purchase_completed') and (
                    enrollment.get('expires_at') is None or enrollment.get('expires_at') > datetime.now(timezone.utc)
                )
            ]

            return {
                "success": True,
                "message": "Login successful",
                "status_code": 200,
                "data": user_dict,
                "access_token": access_token,
                "refresh_token": refresh_token
            }
        except Exception as e:
            logger.error(f"Email/password login failed: {str(e)}", exc_info=True)
            return {
                "success": False, 
                "message": "An error occurred while processing your request",
                "status_code": 500
            }
        

    async def verify_account(self, user_id: str, otp: str) -> dict:
        """
        Verify a user's account using an OTP.
        
        Args:
            user_id: UUID of the user to verify
            otp: One-time password sent to user's email
        
        Returns:
            dict: Response dictionary with success status and message
        """
        try:
            user = self._userRepository.get_by_id(user_id)
            if not user:
                return {"success": False, "message": "User not found", "status_code": 404}
            
            if user.account_verified:
                return {"success": False, "message": "Account already verified", "status_code": 400}

            otp_record = self._userRepository.get_latest_otp(user.Id)
            if not otp_record:
                return {"success": False, "message": "No OTP found. Please request a new one.", "status_code": 404}
            
            if otp_record.used:
                return {"success": False, "message": "OTP has already been used. Please request a new one.", "status_code": 400}

            if otp_record.expires_at < datetime.datetime.now():
                return {"success": False, "message": "OTP has expired. Please request a new one.", "status_code": 400}

            if not checkpw(otp.encode("utf-8"), otp_record.otp_hash.encode("utf-8")):
                return {"success": False, "message": "Invalid OTP", "status_code": 401}

            # Mark OTP as used
            self._userRepository.mark_otp_as_used(otp_record.Id)

            # Verify the user's account
            updated_user = self._userRepository.verify_user_account(user.Id)
            self._userRepository.delete_expired_user_otps(user.Id)

            access_token, refresh_token = self._generate_tokens(user)

            asyncio.create_task(
                self._mailing_service.send_welcome_email(
                    user.email, 
                    user.first_name or "User"
                )
            )

            return {
                "success": True, 
                "data": updated_user, 
                "message": "Account verified successfully", 
                "status_code": 200,
                "access_token": access_token,
                "refresh_token": refresh_token
                }
        except Exception as e:
            logger.error(f"Account verification failed: {str(e)}", exc_info=True)
            return {
                "success": False, 
                "message": "An error occurred while processing your request",
                "status_code": 500
            }
        

    async def request_password_reset(self, email: str) -> dict:
        """
        Request a password reset by sending an OTP to the user's email.
        
        Args:
            email: User's email address
        
        Returns:
            dict: Response dictionary with success status and user data
        """
        try:
            user = self._userRepository.get_by_email(email)
            if not user:
                return {"success": False, "message": "User not found", "status_code": 404}
            
            otp = self._generate_otp()
            asyncio.create_task(
                self._mailing_service.send_password_reset_email(
                    user.email, 
                    otp, 
                    user.first_name or "User"
                )
            )
            self._userRepository.create_otp(user.Id, hashpw(otp.encode("utf-8"), gensalt()).decode("utf-8"))
            self._userRepository.delete_expired_user_otps(user.Id)

            return {
                "success": True, 
                "message": "OTP sent to your email. OTP valid for 10 minutes.", 
                "data": UserResponse.model_validate(user).model_dump(),
                "status_code": 200
            }

        except Exception as e:
            logger.error(f"Password reset request failed: {str(e)}", exc_info=True)
            return {
                "success": False, 
                "message": "An error occurred while processing your request",
                "status_code": 500
            }
        
    def reset_password(self, user_id: str, otp: str, new_password: str) -> dict:
        """
        Reset a user's password using an OTP.
        
        Args:
            user_id: UUID of the user
            otp: One-time password sent to user's email
            new_password: New password to set for the user
        
        Returns:
            dict: Response dictionary with success status and message
        """
        try:
            user = self._userRepository.get_by_id(user_id)
            if not user:
                return {"success": False, "message": "User not found", "status_code": 404}

            otp_record = self._userRepository.get_latest_otp(user.Id)

            if not otp_record:
                return {"success": False, "message": "No OTP found. Please request a new one.", "status_code": 404}
            
            if otp_record.used:
                return {"success": False, "message": "OTP has already been used. Please request a new one.", "status_code": 400}

            if otp_record.expires_at < datetime.datetime.now():
                return {"success": False, "message": "OTP has expired. Please request a new one.", "status_code": 400}

            if not checkpw(otp.encode("utf-8"), otp_record.otp_hash.encode("utf-8")):
                return {"success": False, "message": "Invalid OTP", "status_code": 401}

            # Mark OTP as used
            self._userRepository.mark_otp_as_used(otp_record.Id)

            # Update the user's password
            self._userRepository.update_password(user.Id, new_password)
            self._userRepository.delete_expired_user_otps(user.Id)

            return {"success": True, "message": "Password reset successfully", "status_code": 200}
        except Exception as e:
            logger.error(f"Password reset failed: {str(e)}", exc_info=True)
            return {
                "success": False, 
                "message": "An error occurred while processing your request",
                "status_code": 500
            }
        

    async def resend_otp(self, user_id: str) -> dict:
        """
        Resend an OTP to the user's email.
        
        Args:
            user_id: UUID of the user requesting OTP resend
        
        Returns:
            dict: Response dictionary with success status and message
        """
        try:
            user = self._userRepository.get_by_id(user_id)
            if not user:
                return {"success": False, "message": "User not found", "status_code": 404}
            
            otp = self._generate_otp()
            asyncio.create_task(
                self._mailing_service.send_otp_email(
                    user.email, 
                    otp, 
                    user.first_name or "User"
                )
            )

            self._userRepository.create_otp(
                user.Id, 
                hashpw(
                    otp.encode("utf-8"), 
                    gensalt()
                ).decode("utf-8")
            )
            self._userRepository.delete_expired_user_otps(user.Id)

            return {"success": True, "message": "OTP resent to your email. OTP valid for 10 minutes.", "status_code": 200}
        except Exception as e:
            logger.error(f"OTP resend failed: {str(e)}", exc_info=True)
            return {
                "success": False, 
                "message": "An error occurred while processing your request",
                "status_code": 500
            }
        


    def obtain_access_token(self, refresh_token: str) -> dict:
        """
        Obtain new access and refresh tokens using a refresh token.
        
        Args:
            refresh_token: Valid refresh token string
        
        Returns:
            dict: Response dictionary with new access and refresh tokens
        """
        user = self._userRepository.get_user_by_refresh_token(refresh_token)
        if not user:
            return {"success": False, "message": "Invalid refresh token", "status_code": 401}

        access_token, new_refresh_token = self._generate_tokens(user)
        self._userRepository.save_refresh_token(new_refresh_token, user.Id)
        self._userRepository.delete_refresh_token(refresh_token)

        user_data = UserResponse.model_validate(user).model_dump()

        return {
            "success": True,
            "status_code": 200,
            "message": "Refresh successful",
            "data": user_data,
            "access_token": access_token,
            "refresh_token": new_refresh_token
        }
    
    def logout_user(self, refresh_token: str) -> dict:
        """
        Logout a user by revoking their refresh token.
        
        Args:
            refresh_token: Refresh token to revoke
        
        Returns:
            dict: Response dictionary with logout status
        """
        if not refresh_token:
            return {"success": False, "message": "No refresh token provided", "status_code": 400}
        
        # Revoke the refresh token in the database
        revoked = self._userRepository.revoke_refresh_token(refresh_token)
        
        if revoked:
            return {
                "success": True,
                "message": "Logged out successfully",
                "status_code": 200
            }
        else:
            return {
                "success": False, 
                "message": "Invalid or already revoked refresh token",
                "status_code": 400
            }

