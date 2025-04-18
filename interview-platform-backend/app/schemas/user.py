# app/schemas/user.py
from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime

# Shared properties
class UserBase(BaseModel):
    email: EmailStr
    full_name: Optional[str] = None
    is_active: bool = True

# Properties to receive via API on creation
class UserCreate(UserBase):
    password: str

# Properties to receive via API on update (optional)
class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    full_name: Optional[str] = None
    password: Optional[str] = None
    is_active: Optional[bool] = None
    is_admin: Optional[bool] = None

# Properties to receive on login
class UserLogin(BaseModel):
    email: EmailStr
    password: str

# Properties shared by models stored in DB
class UserInDBBase(UserBase):
    id: int
    is_admin: bool = False
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True # Changed from from_attributes=True for compatibility if needed

# Properties to return to client (never include password hash)
class UserResponse(UserInDBBase):
    pass

# Properties stored in DB (including password hash)
class UserInDB(UserInDBBase):
    hashed_password: str