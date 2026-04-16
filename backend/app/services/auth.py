from __future__ import annotations

import psycopg2.extensions

from fastapi import Request

from app.core.errors import BadRequestError, UnauthorizedError
from app.core.security import create_access_token, verify_password
from app.repositories import login_attempts, users


def login(
    conn: psycopg2.extensions.connection,
    *,
    username: str,
    password: str,
    request: Request | None = None,
) -> dict:
    ip_address = request.client.host if request and request.client else None
    user = users.get_by_username(conn, username)

    if user is None or not verify_password(password, user["password_hash"]):
        login_attempts.create_attempt(
            conn,
            username=username,
            user_id=user["id"] if user else None,
            success=False,
            reason="Invalid username or password.",
            ip_address=ip_address,
        )
        raise UnauthorizedError("Invalid username or password.")

    if not user["is_active"]:
        login_attempts.create_attempt(
            conn,
            username=username,
            user_id=user["id"],
            success=False,
            reason="User is inactive.",
            ip_address=ip_address,
        )
        raise UnauthorizedError("User account is inactive.")

    login_attempts.create_attempt(
        conn,
        username=username,
        user_id=user["id"],
        success=True,
        reason="Login successful.",
        ip_address=ip_address,
    )

    access_token, expires_in_seconds = create_access_token(user["username"])
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "expires_in_seconds": expires_in_seconds,
        "user": {
            "id": user["id"],
            "email": user["username"],
            "full_name": user["full_name"],
            "role": user["role"],
            "is_active": user["is_active"],
            "created_at": user["created_at"],
        },
    }


def signup(
    conn: psycopg2.extensions.connection,
    *,
    username: str,
    password: str,
    full_name: str | None = None,
) -> dict:
    # Check if username already exists
    existing_user = users.get_by_username(conn, username)
    if existing_user is not None:
        raise BadRequestError("Username already exists.")

    # Create the new user
    user = users.create_user(
        conn,
        username=username,
        password=password,
        full_name=full_name,
        role="clinician",
        is_active=True,
    )

    # Generate access token for the new user
    access_token, expires_in_seconds = create_access_token(user["username"])
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "expires_in_seconds": expires_in_seconds,
        "user": {
            "id": user["id"],
            "email": user["username"],
            "full_name": user["full_name"],
            "role": user["role"],
            "is_active": user["is_active"],
            "created_at": user["created_at"],
        },
    }
