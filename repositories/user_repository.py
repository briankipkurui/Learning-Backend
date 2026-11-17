from datetime import datetime, timedelta, timezone
from sqlalchemy.orm import Session, selectinload, joinedload
from schemas import UserCreate, UserUpdate, LearnerProfileBase, CreateUserWithPassword
from models import (
    UserModel, RefreshTokenModel,
    LearnerProfileModel, AdminProfileModel,
    OTPModel, AgeGroupModel, EnrollmentModel,
    CourseModel, ModuleModel, LessonModel
)
from typing import List, Optional
from uuid import UUID
from bcrypt import hashpw, gensalt

class UserRepository:
    def __init__(self, db: Session):
        """
        Initialize user repository with database session.
        
        Args:
            db: SQLAlchemy database session
        """
        self.db = db
    
    def get_all(self, limit: int = 10, offset: int = 0, search: str | None = None) -> dict:
        """
        Get all users with pagination and optional search filtering.
        
        Args:
            limit: Maximum number of users to return (default: 10)
            offset: Number of users to skip for pagination (default: 0)
            search: Optional search term to filter by name or email
        
        Returns:
            dict: Contains users list, total count, pagination metadata
        """
        from sqlalchemy import or_
        
        base_query = self.db.query(UserModel).options(
            selectinload(UserModel.learner_profile)\
                .joinedload(LearnerProfileModel.age_group),
            selectinload(UserModel.learner_profile)\
                .joinedload(LearnerProfileModel.profession),
            selectinload(UserModel.admin_profile)
        )
        
        if search:
            search_term = f"%{search}%"
            base_query = base_query.filter(
                or_(
                    UserModel.first_name.ilike(search_term),
                    UserModel.last_name.ilike(search_term),
                    UserModel.email.ilike(search_term)
                )
            )
        
        # Get total count
        total_count = base_query.count()
        
        # Paginated results
        users = base_query.order_by(UserModel.first_name)\
            .offset(offset)\
            .limit(limit)\
            .all()
        
        return {
            'users': users,
            'total': total_count,
            'limit': limit,
            'offset': offset,
            'has_next': offset + limit < total_count,
            'has_prev': offset > 0
        }
    
    def get_by_id(self, user_id: UUID) -> Optional[UserModel]:
        """
        Get user by their UUID with related profiles and enrollments.
        
        Args:
            user_id: UUID of the user
        
        Returns:
            UserModel: User object with profiles loaded, or None if not found
        """
        return (
            self.db.query(UserModel)
            .options(
                joinedload(UserModel.learner_profile)
                    .joinedload(LearnerProfileModel.age_group),
                joinedload(UserModel.learner_profile)
                    .joinedload(LearnerProfileModel.profession),
                joinedload(UserModel.admin_profile),
                selectinload(UserModel.enrollments)
                    .joinedload(EnrollmentModel.enrolled_course)
            )
            .filter(UserModel.Id == user_id)
            .first()
        )
    
    def get_by_email(self, email: str) -> Optional[UserModel]:
        """
        Get user by their email address with related profiles and enrollments.
        
        Args:
            email: Email address of the user
        
        Returns:
            UserModel: User object with profiles loaded, or None if not found
        """
        return (
            self.db.query(UserModel)
            .options(
                joinedload(UserModel.learner_profile)
                    .joinedload(LearnerProfileModel.age_group),
                joinedload(UserModel.learner_profile)
                    .joinedload(LearnerProfileModel.profession),
                joinedload(UserModel.admin_profile),
                selectinload(UserModel.enrollments)
                    .joinedload(EnrollmentModel.enrolled_course)
            )
            .filter(UserModel.email == email)
            .first()
        )
    
    def create_user_with_password(self, user_data: CreateUserWithPassword) -> UserModel:
        """
        Create a new user with password authentication and appropriate profile.
        
        Args:
            user_data: User creation data including password
        
        Returns:
            UserModel: The created user with associated profile
        """
        # Convert Pydantic model to dict
        user_dict = user_data.model_dump()
        password = user_dict.pop("password")
        
        # Hash the password before storing it
        password_hash = hashpw(password.encode("utf-8"), gensalt())
        
        db_user = UserModel(**user_dict, password_hash=password_hash.decode("utf-8"))
        self.db.add(db_user)
        self.db.commit()
        self.db.refresh(db_user)
        
        # Create appropriate profile based on user type
        if db_user.user_type == "Learner":
            profile = LearnerProfileModel(user_id=db_user.Id)
            self.db.add(profile)
        elif db_user.user_type == "Admin":
            profile = AdminProfileModel(user_id=db_user.Id)
            self.db.add(profile)
        
        self.db.commit()
        self.db.refresh(db_user)
        return db_user
    
    def create(self, user_data: UserCreate) -> UserModel:
        """
        Create a new user without password (OAuth users) and appropriate profile.
        
        Args:
            user_data: User creation data without password
        
        Returns:
            UserModel: The created user with associated profile
        """
        # Convert Pydantic model to dict
        user_dict = user_data.model_dump()
        
        db_user = UserModel(**user_dict)
        self.db.add(db_user)
        self.db.commit()
        self.db.refresh(db_user)
        
        # Create appropriate profile based on user type
        if db_user.user_type == "Learner":
            profile = LearnerProfileModel(user_id=db_user.Id)
            self.db.add(profile)
        elif db_user.user_type == "Admin":
            profile = AdminProfileModel(user_id=db_user.Id)
            self.db.add(profile)
        
        self.db.commit()
        self.db.refresh(db_user)
        return db_user
    
    def update(self, user_id: UUID, user_data: UserUpdate) -> Optional[UserModel]:
        """
        Update user information.
        
        Args:
            user_id: UUID of the user to update
            user_data: Updated user data
        
        Returns:
            UserModel: Updated user object, or None if not found
        """
        db_user = self.get_by_id(user_id)
        if not db_user:
            return None

        update_data = user_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_user, field, value)

        self.db.commit()
        self.db.refresh(db_user)
        return db_user
    
    def delete(self, user_id: UUID) -> bool:
        """
        Delete a user by their UUID.
        
        Args:
            user_id: UUID of the user to delete
        
        Returns:
            bool: True if user was deleted, False if not found
        """
        db_user = self.get_by_id(user_id)
        if not db_user:
            return False
        
        self.db.delete(db_user)
        self.db.commit()
        return True
    
    def get_learner_profile(self, user_id: UUID) -> Optional[LearnerProfileModel]:
        """
        Get learner profile for a user with related age group and profession.
        
        Args:
            user_id: UUID of the user
        
        Returns:
            LearnerProfileModel: Learner profile with relations, or None if not found
        """
        return self.db.query(
            LearnerProfileModel,
        )\
        .options(
            joinedload(LearnerProfileModel.age_group),
            joinedload(LearnerProfileModel.profession)
        )\
        .filter(
            LearnerProfileModel.user_id == user_id
        )\
        .first()

    def update_learner_profile(self, user_id: UUID, profile_data: LearnerProfileBase) -> Optional[LearnerProfileBase]:
        """
        Update learner profile information.
        
        Args:
            user_id: UUID of the user
            profile_data: Updated learner profile data
        
        Returns:
            LearnerProfileBase: Updated profile, or None if not found
        """
        learner_profile = self.get_learner_profile(user_id)
        if not learner_profile:
            return None

        update_data = profile_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(learner_profile, field, value)

        self.db.commit()
        self.db.refresh(learner_profile)
        return learner_profile

    def save_refresh_token(self, token: str, user_id: UUID) -> bool:
        """
        Save a refresh token for a user.
        
        Args:
            token: Refresh token hash
            user_id: UUID of the user
        
        Returns:
            bool: True if token was saved successfully
        """
        db_token = RefreshTokenModel(token_hash=token, user_id=user_id)
        self.db.add(db_token)
        self.db.commit()
        return True

    def revoke_refresh_token(self, token: str) -> bool:
        """
        Revoke a refresh token by marking it as revoked.
        
        Args:
            token: Refresh token hash to revoke
        
        Returns:
            bool: True if token was revoked successfully
        """
        db_token = self.db.query(RefreshTokenModel).filter(RefreshTokenModel.token_hash == token).first()
        if not db_token:
            return False
        db_token.revoked = True
        db_token.revoked_at = datetime.now()
        self.db.commit()
        return True
    
    def delete_refresh_token(self, token: str) -> bool:
        """
        Delete a refresh token from database.
        
        Args:
            token: Refresh token hash to delete
        
        Returns:
            bool: True if token was deleted successfully
        """
        token_obj = self.db.query(RefreshTokenModel).filter(RefreshTokenModel.token_hash == token).first()
        if not token_obj:
            return False
        self.db.delete(token_obj)
        self.db.commit()
        return True

    def get_user_by_refresh_token(self, token: str) -> Optional[UserModel]:
        """
        Get user associated with a refresh token if valid.
        
        Args:
            token: Refresh token hash
        
        Returns:
            UserModel: User object if token is valid, not revoked, and not expired, None otherwise
        """
        db_token = self.db.query(RefreshTokenModel).filter(RefreshTokenModel.token_hash == token).first()
        if not db_token or db_token.revoked:
            return None
        
        # Check if token has expired
        if db_token.expires_at < datetime.now():
            return None

        return self.get_by_id(db_token.user_id)
    
    def change_user_status(self, user_id: UUID, is_active: bool) -> Optional[UserModel]:
        """
        Change user's active status.
        
        Args:
            user_id: UUID of the user
            is_active: New active status (True for active, False for inactive)
        
        Returns:
            UserModel: Updated user object, or None if not found
        """
        user = self.get_by_id(user_id)
        if not user:
            return None
        user.is_active = is_active
        self.db.commit()
        self.db.refresh(user)
        return user
    
    def verify_user_account(self, user_id: UUID) -> Optional[UserModel]:
        """
        Verify a user's email account.
        
        Args:
            user_id: UUID of the user
        
        Returns:
            UserModel: Updated user with verified account and learner_profile loaded, or None if not found
        """
        user = self.get_by_id(user_id)
        if not user:
            return None
        user.account_verified = True
        self.db.commit()
        # Refresh with relationships loaded
        self.db.refresh(user, ['learner_profile', 'admin_profile'])
        return user
    
    def create_otp(self, user_id: UUID, otp_hash: str) -> bool:
        """
        Create a new OTP for user with 10-minute expiration.
        
        Args:
            user_id: UUID of the user
            otp_hash: Hashed OTP value
        
        Returns:
            bool: True if OTP was created successfully
        """
        otp_entry = OTPModel(user_id=user_id, otp_hash=otp_hash, expires_at=datetime.now() + timedelta(minutes=10))
        self.db.add(otp_entry)
        self.db.commit()
        return True
    
    def get_latest_otp(self, user_id: UUID) -> Optional[OTPModel]:
        """
        Get the latest non-expired OTP for a user.
        
        Args:
            user_id: UUID of the user
        
        Returns:
            OTPModel: Latest OTP if exists and not expired, None otherwise
        """
        return (
            self.db.query(OTPModel)
            .filter(
                OTPModel.user_id == user_id,
                OTPModel.expires_at > datetime.now()
            ) \
            .order_by(OTPModel.expires_at.desc()) \
            .first()
        )
    
    def mark_otp_as_used(self, otp_id: UUID) -> bool:
        """
        Mark an OTP as used to prevent reuse.
        
        Args:
            otp_id: UUID of the OTP
        
        Returns:
            bool: True if OTP was marked as used, False if not found
        """
        otp_entry = self.db.query(OTPModel).filter(OTPModel.Id == otp_id).first()
        if not otp_entry:
            return False
        otp_entry.used = True
        self.db.commit()
        return True
    
    def update_password(self, user_id: UUID, new_password: str) -> bool:
        """
        Update user's password with hashed value.
        
        Args:
            user_id: UUID of the user
            new_password: New password (will be hashed)
        
        Returns:
            bool: True if password was updated, False if user not found
        """
        user = self.get_by_id(user_id)
        if not user:
            return False
        
        password_hash = hashpw(new_password.encode("utf-8"), gensalt())
        
        user.password_hash = password_hash.decode("utf-8")
        self.db.commit()
        return True

    def delete_expired_user_otps(self, user_id: UUID) -> int:
        """
        Delete all expired OTPs for a user.
        
        Args:
            user_id: UUID of the user
        
        Returns:
            int: Number of OTPs deleted
        """
        expired_otps = self.db.query(OTPModel).filter(OTPModel.expires_at < datetime.now(), OTPModel.user_id == user_id).all()
        count = len(expired_otps)
        for otp in expired_otps:
            self.db.delete(otp)
        self.db.commit()
        return count
    
    def fetch_age_groups(self) -> List[AgeGroupModel]:
        """
        Get all age groups ordered by sort order.
        
        Returns:
            List[AgeGroupModel]: List of all age group options
        """
        return self.db.query(AgeGroupModel).order_by(AgeGroupModel.sort_order.asc()).all()
    
    def get_my_courses(self, user_id: UUID) -> List[UserModel]:
        """
        Get user's enrolled courses with modules and lessons.
        
        Args:
            user_id: UUID of the user
        
        Returns:
            List[UserModel]: User with enrolled courses and their content
        """
        return (
            self.db.query(UserModel)
            .options(
                selectinload(EnrollmentModel.enrolled_course)
                .selectinload(CourseModel.modules)
                .selectinload(ModuleModel.lessons)
            )
            .filter(EnrollmentModel.user_id == user_id)
            .all()
        )
    
    def get_user_enrollments(self, user_id: UUID) -> List[EnrollmentModel]:
        """
        Get all enrollments for a user with course details and progress.
        
        Args:
            user_id: UUID of the user
        
        Returns:
            List[EnrollmentModel]: List of enrollments with courses and progress
        """
        return (
            self.db.query(EnrollmentModel)
            .options(
                selectinload(EnrollmentModel.enrolled_course)
                .selectinload(CourseModel.modules)
                .selectinload(ModuleModel.lessons)
            )
            .filter(EnrollmentModel.user_id == user_id)
            .all()
        )
    
    def fetch_public_profile(self, user_id: UUID) -> Optional[UserModel]:
        """
        Get user's public profile information with learner profile.
        
        Args:
            user_id: UUID of the user
        
        Returns:
            UserModel: User with public profile data, or None if not found
        """
        return (
            self.db.query(UserModel)
            .options(
                joinedload(UserModel.learner_profile)
                    .joinedload(LearnerProfileModel.age_group),
                joinedload(UserModel.learner_profile)
                    .joinedload(LearnerProfileModel.profession),
                selectinload(UserModel.enrollments)
                    .joinedload(EnrollmentModel.enrolled_course),
                selectinload(UserModel.enrollments)
                    .joinedload(EnrollmentModel.certificate)
            )
            .filter(UserModel.Id == user_id)
            .first()
        )
    