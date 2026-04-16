from __future__ import annotations

from pydantic import BaseModel, field_validator

from app.schemas.users import UserResponse


class LoginRequest(BaseModel):
    email: str
    password: str

    @field_validator("email", "password")
    @classmethod
    def validate_non_empty(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("Field cannot be empty.")
        return cleaned


class SignupRequest(BaseModel):
    email: str
    password: str
    full_name: str | None = None

    @field_validator("email", "password")
    @classmethod
    def validate_non_empty(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("Field cannot be empty.")
        return cleaned

    @field_validator("password")
    @classmethod
    def validate_password_strength(cls, value: str) -> str:
        if len(value) < 8:
            raise ValueError("Password must be at least 8 characters long.")
        return value


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in_seconds: int
    user: UserResponse
