from __future__ import annotations

from pydantic import BaseModel


class UserResponse(BaseModel):
    id: str
    email: str
    full_name: str | None = None
    role: str
    is_active: bool
    created_at: str
