from __future__ import annotations

import secrets
import string

import psycopg2.extensions
from fastapi import APIRouter, Depends, Query

from app.api.deps import get_current_admin
from app.core.errors import BadRequestError, ConflictError
from app.data.database import get_db
from app.repositories import admin_audit_log as audit_repo
from app.repositories import triage_sessions as sessions_repo
from app.repositories import users as users_repo
from app.schemas.admin import (
    AdminSessionItem,
    AdminSessionsResponse,
    ChangeLogEntry,
    ChangeLogResponse,
    CreateUserRequest,
    CreateUserResponse,
    UpdateUserRequest,
    UserListItem,
    UsersListResponse,
)

router = APIRouter(prefix="/admin", tags=["admin"])

_PASSWORD_CHARS = string.ascii_letters + string.digits + "!@#$%^&*"


def _generate_temp_password(length: int = 12) -> str:
    return "".join(secrets.choice(_PASSWORD_CHARS) for _ in range(length))


def _build_user_item(
    conn: psycopg2.extensions.connection,
    user: dict,
) -> UserListItem:
    return UserListItem(
        id=user["id"],
        email=user["username"],
        full_name=user["full_name"],
        role=user["role"],
        is_active=user["is_active"],
        created_at=user["created_at"],
        last_login=users_repo.get_last_login(conn, user["id"]),
    )


# ──────────────────────────────────────────────
#  User Management
# ──────────────────────────────────────────────

@router.get("/users", response_model=UsersListResponse)
def list_users(
    search: str | None = Query(default=None),
    conn: psycopg2.extensions.connection = Depends(get_db),
    admin: dict = Depends(get_current_admin),
) -> UsersListResponse:
    all_users = users_repo.list_all_users(conn, search=search)
    items = [_build_user_item(conn, u) for u in all_users]
    return UsersListResponse(items=items, total=len(items))


@router.get("/users/{user_id}", response_model=UserListItem)
def get_user(
    user_id: str,
    conn: psycopg2.extensions.connection = Depends(get_db),
    admin: dict = Depends(get_current_admin),
) -> UserListItem:
    user = users_repo.get_by_id(conn, user_id)
    if user is None:
        raise BadRequestError("User not found.")
    return _build_user_item(conn, user)


@router.post("/users", response_model=CreateUserResponse, status_code=201)
def create_user(
    payload: CreateUserRequest,
    conn: psycopg2.extensions.connection = Depends(get_db),
    admin: dict = Depends(get_current_admin),
) -> CreateUserResponse:
    existing = users_repo.get_by_username(conn, payload.email)
    if existing is not None:
        raise ConflictError("A user with that email already exists.")

    temp_password = _generate_temp_password()
    user = users_repo.create_user(
        conn,
        username=payload.email,
        password=temp_password,
        full_name=payload.full_name,
        role=payload.role,
        is_active=True,
    )

    role_label = payload.role.capitalize()
    audit_repo.create_log(
        conn,
        admin_id=admin["id"],
        admin_username=admin["username"],
        action_type="user_created",
        target_user_id=user["id"],
        target_name=payload.full_name,
        details=f"New {role_label} account created for {payload.email}.",
    )

    return CreateUserResponse(
        user=_build_user_item(conn, user),
        temporary_password=temp_password,
    )


@router.put("/users/{user_id}", response_model=UserListItem)
def update_user(
    user_id: str,
    payload: UpdateUserRequest,
    conn: psycopg2.extensions.connection = Depends(get_db),
    admin: dict = Depends(get_current_admin),
) -> UserListItem:
    existing = users_repo.get_by_id(conn, user_id)
    if existing is None:
        raise BadRequestError("User not found.")

    updated = users_repo.update_user(
        conn,
        user_id,
        full_name=payload.full_name,
        role=payload.role,
    )
    assert updated is not None

    if payload.role is not None and payload.role != existing["role"]:
        audit_repo.create_log(
            conn,
            admin_id=admin["id"],
            admin_username=admin["username"],
            action_type="role_modified",
            target_user_id=user_id,
            target_name=updated["full_name"] or updated["username"],
            details=f"Role updated from {existing['role'].capitalize()} to {payload.role.capitalize()}.",
        )

    return _build_user_item(conn, updated)


@router.post("/users/{user_id}/deactivate", response_model=UserListItem)
def deactivate_user(
    user_id: str,
    conn: psycopg2.extensions.connection = Depends(get_db),
    admin: dict = Depends(get_current_admin),
) -> UserListItem:
    if user_id == admin["id"]:
        raise BadRequestError("Admins cannot deactivate their own account.")

    existing = users_repo.get_by_id(conn, user_id)
    if existing is None:
        raise BadRequestError("User not found.")
    if not existing["is_active"]:
        raise BadRequestError("User is already inactive.")

    updated = users_repo.update_user(conn, user_id, is_active=False)
    assert updated is not None

    audit_repo.create_log(
        conn,
        admin_id=admin["id"],
        admin_username=admin["username"],
        action_type="user_deactivated",
        target_user_id=user_id,
        target_name=updated["full_name"] or updated["username"],
        details=f"{updated['role'].capitalize()} account deactivated.",
    )

    return _build_user_item(conn, updated)


@router.post("/users/{user_id}/reactivate", response_model=UserListItem)
def reactivate_user(
    user_id: str,
    conn: psycopg2.extensions.connection = Depends(get_db),
    admin: dict = Depends(get_current_admin),
) -> UserListItem:
    existing = users_repo.get_by_id(conn, user_id)
    if existing is None:
        raise BadRequestError("User not found.")
    if existing["is_active"]:
        raise BadRequestError("User is already active.")

    updated = users_repo.update_user(conn, user_id, is_active=True)
    assert updated is not None

    audit_repo.create_log(
        conn,
        admin_id=admin["id"],
        admin_username=admin["username"],
        action_type="user_reactivated",
        target_user_id=user_id,
        target_name=updated["full_name"] or updated["username"],
        details=f"{updated['role'].capitalize()} account reactivated.",
    )

    return _build_user_item(conn, updated)


@router.delete("/users/{user_id}", status_code=204)
def delete_user(
    user_id: str,
    conn: psycopg2.extensions.connection = Depends(get_db),
    admin: dict = Depends(get_current_admin),
) -> None:
    if user_id == admin["id"]:
        raise BadRequestError("Admins cannot delete their own account.")

    existing = users_repo.get_by_id(conn, user_id)
    if existing is None:
        raise BadRequestError("User not found.")

    target_name = existing["full_name"] or existing["username"]
    deleted = users_repo.delete_user(conn, user_id)
    if not deleted:
        raise BadRequestError("User could not be deleted.")

    audit_repo.create_log(
        conn,
        admin_id=admin["id"],
        admin_username=admin["username"],
        action_type="user_deleted",
        target_user_id=None,
        target_name=target_name,
        details=f"{existing['role'].capitalize()} account permanently deleted.",
    )


# ──────────────────────────────────────────────
#  Change Log
# ──────────────────────────────────────────────

@router.get("/change-log", response_model=ChangeLogResponse)
def get_change_log(
    from_date: str | None = Query(default=None, description="ISO date string, e.g. 2024-03-01"),
    to_date: str | None = Query(default=None, description="ISO date string, e.g. 2024-03-31"),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    conn: psycopg2.extensions.connection = Depends(get_db),
    admin: dict = Depends(get_current_admin),
) -> ChangeLogResponse:
    logs = audit_repo.list_logs(
        conn, from_date=from_date, to_date=to_date, limit=limit, offset=offset
    )
    total = audit_repo.count_logs(conn, from_date=from_date, to_date=to_date)
    items = [
        ChangeLogEntry(
            id=log["id"],
            timestamp=log["timestamp"],
            admin_user=log["admin_username"],
            action_type=log["action_type"],
            target=log["target_name"],
            details=log["details"],
        )
        for log in logs
    ]
    return ChangeLogResponse(items=items, total=total)


# ──────────────────────────────────────────────
#  Session History
# ──────────────────────────────────────────────

@router.get("/sessions", response_model=AdminSessionsResponse)
def list_sessions(
    search: str | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    conn: psycopg2.extensions.connection = Depends(get_db),
    admin: dict = Depends(get_current_admin),
) -> AdminSessionsResponse:
    rows = sessions_repo.list_completed_history(
        conn, search=search, limit=limit, offset=offset
    )
    total = sessions_repo.count_completed_history(conn, search=search)
    items = [
        AdminSessionItem(
            session_id=r["session_id"],
            started_at=r["started_at"],
            ended_at=r.get("ended_at"),
            duration_seconds=r.get("duration_seconds"),
            patient_name=r["patient_name"],
            mrn=r["mrn"],
            patient_language=r["patient_language"],
            ats_category=r.get("ats_category"),
            avg_translation_confidence=r.get("avg_translation_confidence"),
        )
        for r in rows
    ]
    return AdminSessionsResponse(items=items, total=total)


@router.delete("/sessions/{session_id}", status_code=204)
def delete_session(
    session_id: str,
    conn: psycopg2.extensions.connection = Depends(get_db),
    admin: dict = Depends(get_current_admin),
) -> None:
    session = sessions_repo.get_by_id(conn, session_id)
    if session is None:
        raise BadRequestError("Session not found.")

    # Retrieve patient info for the audit log before deletion.
    with conn.cursor() as cursor:
        cursor.execute(
            "SELECT p.full_name, p.mrn FROM patients p"
            " JOIN triage_sessions s ON s.patient_id = p.id"
            " WHERE s.id = %s",
            (session_id,),
        )
        row = cursor.fetchone()
    patient_label = f"{row[0]} ({row[1]})" if row else session_id

    with conn.cursor() as cursor:
        cursor.execute(
            "UPDATE translation_logs SET session_id = %s WHERE session_id = %s",
            (None, session_id),
        )
        cursor.execute("DELETE FROM triage_sessions WHERE id = %s", (session_id,))
    conn.commit()

    audit_repo.create_log(
        conn,
        admin_id=admin["id"],
        admin_username=admin["username"],
        action_type="session_deleted",
        target_user_id=None,
        target_name=patient_label,
        details="Session transcript deleted by administrator.",
    )
