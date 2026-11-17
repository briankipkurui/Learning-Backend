"""
JWT Authentication middleware for protecting routes
"""
import jwt
from fastapi import HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from dependencies import get_db
from models import UserModel
from uuid import UUID
import os
from dotenv import load_dotenv

load_dotenv()

security = HTTPBearer()

def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> UserModel:
    """
    Verify JWT token and return the current user.
    
    Args:
        credentials: JWT token from Authorization header
        db: Database session
        
    Returns:
        UserModel: Current authenticated user
        
    Raises:
        HTTPException: If token is invalid or user not found
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid Credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    if not credentials:
        raise credentials_exception

    try:
        # Get JWT secret key
        secret_key = os.getenv("JWT_SECRET_KEY")
        if not secret_key:
            raise credentials_exception
            
        # Decode JWT token
        payload = jwt.decode(
            credentials.credentials, 
            secret_key, 
            algorithms=["HS256"]
        )
        
        # Extract user ID from token
        user_id_str: str = payload.get("sub")
        if user_id_str is None:
            raise credentials_exception
            
        # Convert string to UUID
        user_id = UUID(user_id_str)
        
    except (jwt.PyJWTError, ValueError):
        raise credentials_exception
    
    # Get user from database
    user = db.query(UserModel).filter(UserModel.Id == user_id).first()
    if user is None:
        raise credentials_exception
        
    # Check if user is active
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is disabled"
        )
    
    return user


def get_current_active_user(current_user: UserModel = Depends(get_current_user)) -> UserModel:
    """
    Get current active user (convenience function).
    
    Args:
        current_user: Current user from get_current_user
        
    Returns:
        UserModel: Current authenticated and active user
    """
    return current_user


def require_admin(current_user: UserModel = Depends(get_current_user)) -> UserModel:
    """
    Require that the current user is an admin.
    
    Args:
        current_user: Current user from get_current_user
        
    Returns:
        UserModel: Current authenticated admin user
        
    Raises:
        HTTPException: If user is not an admin
    """
    if current_user.user_type != "Admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    return current_user


def require_learner(current_user: UserModel = Depends(get_current_user)) -> UserModel:
    """
    Require that the current user is a learner.
    
    Args:
        current_user: Current user from get_current_user
        
    Returns:
        UserModel: Current authenticated learner user
        
    Raises:
        HTTPException: If user is not a learner
    """
    if current_user.user_type != "Learner":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Learner access required"
        )
    return current_user
