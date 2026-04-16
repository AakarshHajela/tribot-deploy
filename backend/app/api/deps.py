from __future__ import annotations

import jwt
import psycopg2.extensions
from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.core.config import get_settings
from app.core.errors import ForbiddenError, UnauthorizedError
from app.core.security import decode_access_token
from app.data.database import get_db
from app.repositories.users import get_by_username

bearer_scheme = HTTPBearer(auto_error=False)


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    conn: psycopg2.extensions.connection = Depends(get_db),
) -> dict:
    if credentials is None or not credentials.credentials:
        raise UnauthorizedError("Not authenticated.")

    token = credentials.credentials
    try:
        payload = decode_access_token(token)
    except jwt.PyJWTError as exc:
        raise UnauthorizedError("Invalid or expired token.") from exc

    username = payload.get("sub")
    if not username:
        raise UnauthorizedError("Invalid token payload.")

    user = get_by_username(conn, username)
    if user is None or not user["is_active"]:
        raise UnauthorizedError("User not found or inactive.")

    return user


def get_current_admin(
    current_user: dict = Depends(get_current_user),
) -> dict:
    if current_user["role"] != "admin":
        raise ForbiddenError("Admin access required. Please use the admin portal.")
    return current_user


def get_current_clinician(
    current_user: dict = Depends(get_current_user),
) -> dict:
    """Grants access to triage/translate/patients/logs routes.
    Both clinicians and admins are allowed — admins have full access to all portals.
    Only rejects users with an unrecognised or future role.
    """
    if current_user["role"] not in ("clinician", "admin"):
        raise ForbiddenError("Triage portal access requires a clinician or admin account.")
    return current_user


def get_demo_clinician_id(
    conn: psycopg2.extensions.connection = Depends(get_db),
) -> str:
    """Used when login is disabled: translation and logs attach to the seeded demo clinician."""
    settings = get_settings()
    user = get_by_username(conn, settings.demo_email)
    if user is None:
        raise HTTPException(
            status_code=503,
            detail="Demo clinician is not available. Set SEED_DEMO_USER=true and restart.",
        )
    return user["id"]
