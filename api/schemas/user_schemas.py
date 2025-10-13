"""
Pydantic schemas for 3-tier user system (Developer, Admin, User)
"""

from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import datetime
import uuid


# ==================== DEVELOPER SCHEMAS ====================

class DeveloperCreate(BaseModel):
    """Schema for creating a Developer"""
    email: EmailStr
    firebase_uid: str = Field(..., min_length=1, max_length=255)
    password_hash: Optional[str] = None


class DeveloperResponse(BaseModel):
    """Schema for Developer responses"""
    id: uuid.UUID
    email: str
    firebase_uid: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ==================== ADMIN SCHEMAS ====================

class AdminCreate(BaseModel):
    """Schema for creating an Admin"""
    email: EmailStr
    firebase_uid: str = Field(..., min_length=1, max_length=255)
    first_name: str = Field(..., min_length=1, max_length=100)
    last_name: str = Field(..., min_length=1, max_length=100)
    password_hash: Optional[str] = None


class AdminUpdate(BaseModel):
    """Schema for updating Admin"""
    first_name: Optional[str] = Field(None, max_length=100)
    last_name: Optional[str] = Field(None, max_length=100)
    is_active: Optional[bool] = None


class AdminResponse(BaseModel):
    """Schema for Admin responses"""
    id: uuid.UUID
    email: str
    firebase_uid: str
    first_name: str
    last_name: str
    full_name: str  # Computed property
    is_active: bool
    created_by_id: uuid.UUID
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ==================== ENTERPRISE SCHEMAS ====================

class EnterpriseCreate(BaseModel):
    """Schema for creating an Enterprise"""
    name: str = Field(..., min_length=1, max_length=255)
    logo_url: Optional[str] = Field(None, max_length=500)
    legal_form: Optional[str] = Field(None, max_length=100)
    siret: Optional[str] = Field(None, min_length=14, max_length=14)


class EnterpriseUpdate(BaseModel):
    """Schema for updating Enterprise"""
    name: Optional[str] = Field(None, max_length=255)
    logo_url: Optional[str] = Field(None, max_length=500)
    legal_form: Optional[str] = Field(None, max_length=100)
    siret: Optional[str] = Field(None, min_length=14, max_length=14)


class EnterpriseResponse(BaseModel):
    """Schema for Enterprise responses"""
    id: uuid.UUID
    admin_id: uuid.UUID
    name: str
    logo_url: Optional[str]
    legal_form: Optional[str]
    siret: Optional[str]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ==================== USER (Employee) SCHEMAS ====================

class UserCreate(BaseModel):
    """Schema for creating a User (employee)"""
    email: Optional[EmailStr] = None
    first_name: str = Field(..., min_length=1, max_length=100)
    last_name: str = Field(..., min_length=1, max_length=100)
    pin_code: str = Field(..., min_length=4, max_length=6, description="4-6 digit PIN code")


class UserUpdate(BaseModel):
    """Schema for updating User"""
    email: Optional[EmailStr] = None
    first_name: Optional[str] = Field(None, max_length=100)
    last_name: Optional[str] = Field(None, max_length=100)
    pin_code: Optional[str] = Field(None, min_length=4, max_length=6)
    is_active: Optional[bool] = None


class UserResponse(BaseModel):
    """Schema for User responses"""
    id: uuid.UUID
    email: Optional[str]
    first_name: str
    last_name: str
    full_name: str  # Computed property
    is_active: bool
    enterprise_id: uuid.UUID
    created_by_id: uuid.UUID
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class UserLoginRequest(BaseModel):
    """Schema for User PIN authentication"""
    pin_code: str = Field(..., min_length=4, max_length=6)
    enterprise_id: uuid.UUID


class UserLoginResponse(BaseModel):
    """Schema for User login response"""
    user: UserResponse
    accessible_rooms: list[uuid.UUID] = []


# ==================== USER_ROOMS SCHEMAS ====================

class UserRoomCreate(BaseModel):
    """Schema for granting room access to user"""
    user_id: uuid.UUID
    room_id: uuid.UUID


class UserRoomResponse(BaseModel):
    """Schema for UserRoom responses"""
    id: uuid.UUID
    user_id: uuid.UUID
    room_id: uuid.UUID
    created_at: datetime

    class Config:
        from_attributes = True
