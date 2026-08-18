from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

class UserBase(BaseModel):
    name: str = Field(..., example="John Doe")
    email: str = Field(..., example="john@example.com")

class UserCreate(UserBase):
    password: str = Field(..., min_length=4, example="secret123")

class UserLogin(BaseModel):
    email: str = Field(..., example="john@example.com")
    password: str = Field(..., example="secret123")

class UserResponse(UserBase):
    id: int
    created_at: datetime
    last_login: Optional[datetime] = None
    status: bool

    class Config:
        from_attributes = True
        orm_mode = True

class OTPVerify(BaseModel):
    email: str = Field(..., example="john@example.com")
    otp: str = Field(..., example="123456")
