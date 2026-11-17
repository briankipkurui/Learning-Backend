from fastapi import APIRouter, HTTPException, Depends, Response, Request
from dependencies import get_auth_service, get_policy_service
from services.auth_service import AuthService
from services.policy_service import PolicyService
from utils.logger import get_logger
from schemas.user import GoogleAuth
from utils.constants import API_PREFIX
import os
from typing import Annotated
from uuid import UUID
from schemas import (
    VerifyAccountRequest, CreateUserWithPassword, 
    ResetPasswordRequest, LoginWithEmail, ResendOTPRequest,
    EmailRequest
)

class AuthController:
    auth_service_dependency = Annotated[AuthService, Depends(get_auth_service)]
    policy_service_dependency = Annotated[PolicyService, Depends(get_policy_service)]

    def __init__(self):
        self.router = APIRouter(prefix=f"{API_PREFIX}/auth", tags=["auth"])
        self.logger = get_logger("app.controllers.auth")
        self._setup_routes()
        self.is_development = os.getenv("ENVIRONMENT", "development") == "development"

    def _setup_routes(self):
        self.router.add_api_route("/login", self.password_email_login, methods=["POST"])
        self.router.add_api_route("/signup", self.email_password_signup, methods=["POST"])
        self.router.add_api_route("/verify", self.verify_account, methods=["POST"])
        self.router.add_api_route("/resend-otp", self.resend_otp, methods=["POST"])
        self.router.add_api_route("/request-password-reset", self.request_password_reset, methods=["POST"])
        self.router.add_api_route("/reset-password", self.reset_password, methods=["PATCH"])
        self.router.add_api_route("/google/login", self.google_login, methods=["POST"])
        self.router.add_api_route("/google/signup", self.google_signup, methods=["POST"])
        self.router.add_api_route("/logout", self.logout, methods=["POST"])
        self.router.add_api_route("/refresh", self.refresh_tokens, methods=["POST"])
        self.logger.info("AuthController routes have been set up.")


    def google_login(self, data: GoogleAuth, auth_service: auth_service_dependency):
        result = auth_service.login_with_google(data.token)
        if not result.get("success"):
            self.logger.error(f"Google login failed: {result.get('message')}")
            raise HTTPException(status_code=result.get("status_code", 500), detail=result.get("message"))

        return result
    
    async def google_signup(
        self, 
        request: Request, 
        data: GoogleAuth, 
        auth_service: auth_service_dependency,
        policy_service: policy_service_dependency
    ):
        result = await auth_service.signup_with_google(data.token)

        if not result.get("success"):
            self.logger.error(f"Google signup failed: {result.get('message')}")
            raise HTTPException(status_code=result.get("status_code", 500), detail=result.get("message"))

        
        # Acknowledge required policies
        user_id = result.get("data", {}).get("Id")
        if user_id:
            user_ip = request.headers.get("x-client-ip")
            user_agent = request.headers.get("user-agent")
            
            # Convert to UUID if it's a string, otherwise use as-is
            if isinstance(user_id, str):
                user_id = UUID(user_id)
            
            policy_result = policy_service.acknowledge_required_policies(
                user_id=user_id,
                user_ip_address=user_ip,
                user_agent=user_agent
            )
            
            if not policy_result.get("success"):
                self.logger.warning(f"Failed to acknowledge policies for user {user_id}: {policy_result.get('message')}")
        
        return result

    def refresh_tokens(self, request: Request, auth_service: auth_service_dependency):
        refresh_token = request.headers.get("x-refresh-token")

        if not refresh_token:
            raise HTTPException(status_code=400, detail="Refresh token is required in 'x-refresh-token' header")
        
        result = auth_service.obtain_access_token(refresh_token)
        if not result.get("success"):
            self.logger.error(f"Token refresh failed: {result.get('message')}")
            raise HTTPException(status_code=result.get("status_code", 500), detail=result.get("message"))

        return result
    

    async def password_email_login(self, loginData: LoginWithEmail, auth_service: auth_service_dependency):

        result = await auth_service.email_password_login(
            loginData.email, 
            loginData.password
        )

        if not result.get("success"):
            self.logger.error(f"Email/password login failed: {result.get('message')}")
            raise HTTPException(status_code=result.get("status_code", 500), detail=result.get("message"))
        

        return result
    
    async def email_password_signup(
        self, 
        request: Request,
        signupData: CreateUserWithPassword, 
        auth_service: auth_service_dependency,
        policy_service: policy_service_dependency
    ):

        result = await auth_service.email_password_signup(signupData)

        if not result.get("success"):
            self.logger.error(f"Email/password signup failed: {result.get('message')}")
            raise HTTPException(status_code=result.get("status_code", 500), detail=result.get("message"))
        
        # Acknowledge required policies
        user_id = result.get("data", {}).get("Id")
        if user_id:
            user_ip = request.headers.get("x-client-ip")
            user_agent = request.headers.get("user-agent")
            
            # Convert to UUID if it's a string, otherwise use as-is
            if isinstance(user_id, str):
                user_id = UUID(user_id)
            
            policy_result = policy_service.acknowledge_required_policies(
                user_id=user_id,
                user_ip_address=user_ip,
                user_agent=user_agent
            )
            
            if not policy_result.get("success"):
                self.logger.warning(f"Failed to acknowledge policies for user {user_id}: {policy_result.get('message')}")

        return result
    
    async def verify_account(self, payload: VerifyAccountRequest, auth_service: auth_service_dependency):

        result = await auth_service.verify_account(payload.user_id, payload.otp)
        if not result.get("success"):
            self.logger.error(f"Email verification failed: {result.get('message')}")
            raise HTTPException(status_code=result.get("status_code", 500), detail=result.get("message"))

        return result

    async def resend_otp(self, payload: ResendOTPRequest, auth_service: auth_service_dependency):
        result = await auth_service.resend_otp(payload.user_id)
        if not result.get("success"):
            self.logger.error(f"OTP resend failed: {result.get('message')}")
            raise HTTPException(status_code=result.get("status_code", 500), detail=result.get("message"))

        return result

    async def request_password_reset(self, payload: EmailRequest, auth_service: auth_service_dependency):
        result = await auth_service.request_password_reset(payload.email)
        if not result.get("success"):
            self.logger.error(f"Password reset request failed: {result.get('message')}")
            raise HTTPException(status_code=result.get("status_code", 500), detail=result.get("message"))
        return result
    

    def reset_password(self, payload: ResetPasswordRequest, auth_service: auth_service_dependency):
        result = auth_service.reset_password(payload.user_id, payload.otp, payload.new_password)
        if not result.get("success"):
            self.logger.error(f"Password reset failed: {result.get('message')}")
            raise HTTPException(status_code=result.get("status_code", 500), detail=result.get("message"))
        return result


    def logout(self, request: Request, response: Response, auth_service: auth_service_dependency):
        """
        Logout user by revoking refresh token and clearing cookie
        """
        # Get refresh token from cookie
        refresh_token = request.cookies.get("refresh_token")
        
        if not refresh_token:
            self.logger.warning("Logout attempt without refresh token cookie")

            response.delete_cookie(
                key="refresh_token",
                path="/"
            )
            return {
                "success": True,
                "message": "Logged out successfully (no active session)",
                "status_code": 200
            }
        
        # Revoke refresh token in database
        result = auth_service.logout_user(refresh_token)
        
        # Always clear the cookie regardless of database result
        response.delete_cookie(
            key="refresh_token",
            path="/"
        )
        
        if result.get("success"):
            self.logger.info("User logged out successfully")
            return {
                "success": True,
                "message": "Logged out successfully",
                "status_code": 200
            }
        else:
            # Even if token was invalid, we cleared the cookie
            self.logger.warning(f"Logout with invalid token: {result.get('message')}")
            return {
                "success": True,
                "message": "Logged out successfully (token was invalid)",
                "status_code": 200
            }
    