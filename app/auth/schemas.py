"""
Pydantic schemas for authentication requests and responses.
"""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, EmailStr


class UserRegisterRequest(BaseModel):
    """Request body for user registration."""
    email: str = Field(..., description="User email address", examples=["operator@pyrosentry.io"])
    username: str = Field(..., min_length=3, max_length=50, description="Username", examples=["operator_01"])
    password: str = Field(..., min_length=8, description="Password (min 8 chars)")
    role: Optional[str] = Field(default="VIEWER", description="User role: ADMIN, OPERATOR, ANALYST, VIEWER")


class UserLoginRequest(BaseModel):
    """Request body for user login."""
    email: str = Field(..., description="User email address")
    password: str = Field(..., description="User password")


class TokenRefreshRequest(BaseModel):
    """Request body for token refresh."""
    refresh_token: str = Field(..., description="Refresh token")


class LogoutRequest(BaseModel):
    """Request body for logout (revoke refresh token)."""
    refresh_token: str = Field(..., description="Refresh token to revoke")


class TokenResponse(BaseModel):
    """Response containing JWT tokens."""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class UserResponse(BaseModel):
    """Public user profile response."""
    id: str
    email: str
    username: str
    role: str
    is_active: bool
    created_at: datetime


class MessageResponse(BaseModel):
    """Generic message response."""
    message: str
