from __future__ import annotations

import psycopg2.extensions
from fastapi import APIRouter, Depends, Request

from app.api.deps import get_current_user
from app.data.database import get_db
from app.schemas.auth import LoginRequest, TokenResponse
from app.schemas.users import UserResponse
from app.services.auth import login as login_service

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=TokenResponse)
def login(
    payload: LoginRequest,
    request: Request,
    conn: psycopg2.extensions.connection = Depends(get_db),
) -> TokenResponse:
    result = login_service(
        conn,
        username=payload.email,
        password=payload.password,
        request=request,
    )
    return TokenResponse(**result)


@router.get("/me", response_model=UserResponse)
def me(current_user: dict = Depends(get_current_user)) -> UserResponse:
    return UserResponse(
        id=current_user["id"],
        email=current_user["username"],
        full_name=current_user["full_name"],
        role=current_user["role"],
        is_active=current_user["is_active"],
        created_at=current_user["created_at"],
    )
