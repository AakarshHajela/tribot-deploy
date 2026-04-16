from __future__ import annotations

from pydantic import BaseModel, field_validator


class CreateUserRequest(BaseModel):
    full_name: str
    email: str
    role: str = "clinician"

    @field_validator("role")
    @classmethod
    def validate_role(cls, v: str) -> str:
        if v not in ("admin", "clinician"):
            raise ValueError("Role must be 'admin' or 'clinician'.")
        return v

    @field_validator("email", "full_name")
    @classmethod
    def validate_non_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Field cannot be empty.")
        return v.strip()


class UpdateUserRequest(BaseModel):
    full_name: str | None = None
    role: str | None = None

    @field_validator("role")
    @classmethod
    def validate_role(cls, v: str | None) -> str | None:
        if v is not None and v not in ("admin", "clinician"):
            raise ValueError("Role must be 'admin' or 'clinician'.")
        return v


class UserListItem(BaseModel):
    id: str
    email: str
    full_name: str | None = None
    role: str
    is_active: bool
    created_at: str
    last_login: str | None = None


class CreateUserResponse(BaseModel):
    user: UserListItem
    temporary_password: str


class UsersListResponse(BaseModel):
    items: list[UserListItem]
    total: int


class ChangeLogEntry(BaseModel):
    id: int
    timestamp: str
    admin_user: str
    action_type: str
    target: str
    details: str


class ChangeLogResponse(BaseModel):
    items: list[ChangeLogEntry]
    total: int


class AdminSessionItem(BaseModel):
    session_id: str
    started_at: str
    ended_at: str | None = None
    duration_seconds: int | None = None
    patient_name: str
    mrn: str
    patient_language: str
    ats_category: int | None = None
    avg_translation_confidence: float | None = None


class AdminSessionsResponse(BaseModel):
    items: list[AdminSessionItem]
    total: int
