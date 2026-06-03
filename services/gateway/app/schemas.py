from enum import StrEnum

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class Role(StrEnum):
    CUSTOMER = "CUSTOMER"
    ADMIN = "ADMIN"


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=6, max_length=128)
    role: Role = Role.CUSTOMER


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    email: EmailStr
    role: str
