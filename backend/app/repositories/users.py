from __future__ import annotations

import psycopg2.extensions
from typing import Any
from uuid import uuid4

from app.core.security import hash_password
from app.core.utils import utcnow_iso


def _row_to_user(row: tuple | None) -> dict[str, Any] | None:
    if row is None:
        return None
    return {
        "id": row[0],
        "username": row[1],
        "full_name": row[2],
        "password_hash": row[3],
        "role": row[4],
        "is_active": bool(row[5]),
        "created_at": row[6],
    }


def get_by_username(conn: psycopg2.extensions.connection, username: str) -> dict[str, Any] | None:
    with conn.cursor() as cursor:
        cursor.execute(
            "SELECT id, username, full_name, password_hash, role, is_active, created_at FROM users WHERE username = %s",
            (username,),
        )
        row = cursor.fetchone()
    return _row_to_user(row)


def get_by_id(conn: psycopg2.extensions.connection, user_id: str) -> dict[str, Any] | None:
    with conn.cursor() as cursor:
        cursor.execute(
            "SELECT id, username, full_name, password_hash, role, is_active, created_at FROM users WHERE id = %s",
            (user_id,),
        )
        row = cursor.fetchone()
    return _row_to_user(row)


def create_user(
    conn: psycopg2.extensions.connection,
    *,
    username: str,
    password: str,
    full_name: str | None = None,
    role: str = "clinician",
    is_active: bool = True,
) -> dict[str, Any]:
    user_id = str(uuid4())
    created_at = utcnow_iso()
    password_hash = hash_password(password)

    with conn.cursor() as cursor:
        cursor.execute(
            '''
            INSERT INTO users (id, username, full_name, password_hash, role, is_active, created_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            ''',
            (
                user_id,
                username,
                full_name,
                password_hash,
                role,
                is_active,
                created_at,
            ),
        )
    conn.commit()
    user = get_by_id(conn, user_id)
    assert user is not None
    return user


def ensure_demo_user(conn: psycopg2.extensions.connection, *, username: str, password: str) -> None:
    existing = get_by_username(conn, username)
    if existing is None:
        create_user(
            conn,
            username=username,
            password=password,
            full_name="Demo Clinician",
            role="clinician",
        )


def ensure_demo_admin(conn: psycopg2.extensions.connection, *, username: str, password: str) -> None:
    existing = get_by_username(conn, username)
    if existing is None:
        create_user(
            conn,
            username=username,
            password=password,
            full_name="Demo Admin",
            role="admin",
        )


def list_all_users(
    conn: psycopg2.extensions.connection,
    *,
    search: str | None = None,
) -> list[dict[str, Any]]:
    query = (
        "SELECT id, username, full_name, password_hash, role, is_active, created_at"
        " FROM users WHERE 1=1"
    )
    params: list[Any] = []
    if search and search.strip():
        pattern = f"%{search.strip()}%"
        query += " AND (username ILIKE %s OR full_name ILIKE %s)"
        params.extend([pattern, pattern])
    query += " ORDER BY created_at DESC"
    with conn.cursor() as cursor:
        cursor.execute(query, tuple(params))
        rows = cursor.fetchall()
    return [u for row in rows if (u := _row_to_user(row)) is not None]


def get_last_login(
    conn: psycopg2.extensions.connection,
    user_id: str,
) -> str | None:
    with conn.cursor() as cursor:
        cursor.execute(
            """
            SELECT timestamp FROM login_attempts
            WHERE user_id = %s AND success = TRUE
            ORDER BY timestamp DESC LIMIT 1
            """,
            (user_id,),
        )
        row = cursor.fetchone()
    return str(row[0]) if row else None


def update_user(
    conn: psycopg2.extensions.connection,
    user_id: str,
    *,
    full_name: str | None = None,
    role: str | None = None,
    is_active: bool | None = None,
) -> dict[str, Any] | None:
    fields: list[str] = []
    params: list[Any] = []
    if full_name is not None:
        fields.append("full_name = %s")
        params.append(full_name)
    if role is not None:
        fields.append("role = %s")
        params.append(role)
    if is_active is not None:
        fields.append("is_active = %s")
        params.append(is_active)
    if not fields:
        return get_by_id(conn, user_id)
    params.append(user_id)
    with conn.cursor() as cursor:
        cursor.execute(
            f"""
            UPDATE users SET {", ".join(fields)} WHERE id = %s
            RETURNING id, username, full_name, password_hash, role, is_active, created_at
            """,
            tuple(params),
        )
        row = cursor.fetchone()
    conn.commit()
    return _row_to_user(row) if row else None


def delete_user(
    conn: psycopg2.extensions.connection,
    user_id: str,
) -> bool:
    with conn.cursor() as cursor:
        cursor.execute(
            "UPDATE translation_logs SET clinician_id = NULL WHERE clinician_id = %s",
            (user_id,),
        )
        cursor.execute(
            "UPDATE triage_sessions SET provider_id = NULL WHERE provider_id = %s",
            (user_id,),
        )
        cursor.execute("DELETE FROM users WHERE id = %s", (user_id,))
        deleted = cursor.rowcount
    conn.commit()
    return deleted > 0
