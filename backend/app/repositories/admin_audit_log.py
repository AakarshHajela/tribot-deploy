from __future__ import annotations

import psycopg2.extensions
from typing import Any

from app.core.utils import utcnow_iso


def _row_to_log(row: tuple) -> dict[str, Any]:
    return {
        "id": row[0],
        "timestamp": row[1],
        "admin_id": row[2],
        "admin_username": row[3],
        "action_type": row[4],
        "target_user_id": row[5],
        "target_name": row[6],
        "details": row[7],
    }


def create_log(
    conn: psycopg2.extensions.connection,
    *,
    admin_id: str,
    admin_username: str,
    action_type: str,
    target_name: str,
    details: str,
    target_user_id: str | None = None,
) -> dict[str, Any]:
    timestamp = utcnow_iso()
    with conn.cursor() as cursor:
        cursor.execute(
            """
            INSERT INTO admin_audit_log
                (timestamp, admin_id, admin_username, action_type, target_user_id, target_name, details)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            RETURNING id, timestamp, admin_id, admin_username, action_type, target_user_id, target_name, details
            """,
            (timestamp, admin_id, admin_username, action_type, target_user_id, target_name, details),
        )
        row = cursor.fetchone()
    conn.commit()
    assert row is not None
    return _row_to_log(row)


def list_logs(
    conn: psycopg2.extensions.connection,
    *,
    from_date: str | None = None,
    to_date: str | None = None,
    limit: int = 50,
    offset: int = 0,
) -> list[dict[str, Any]]:
    query = (
        "SELECT id, timestamp, admin_id, admin_username, action_type,"
        " target_user_id, target_name, details"
        " FROM admin_audit_log WHERE 1=1"
    )
    params: list[Any] = []
    if from_date:
        query += " AND timestamp >= %s"
        params.append(from_date)
    if to_date:
        query += " AND timestamp <= %s"
        params.append(to_date)
    query += " ORDER BY timestamp DESC LIMIT %s OFFSET %s"
    params.extend([limit, offset])
    with conn.cursor() as cursor:
        cursor.execute(query, tuple(params))
        rows = cursor.fetchall()
    return [_row_to_log(row) for row in rows]


def count_logs(
    conn: psycopg2.extensions.connection,
    *,
    from_date: str | None = None,
    to_date: str | None = None,
) -> int:
    query = "SELECT COUNT(*) FROM admin_audit_log WHERE 1=1"
    params: list[Any] = []
    if from_date:
        query += " AND timestamp >= %s"
        params.append(from_date)
    if to_date:
        query += " AND timestamp <= %s"
        params.append(to_date)
    with conn.cursor() as cursor:
        cursor.execute(query, tuple(params))
        row = cursor.fetchone()
    return int(row[0]) if row and row[0] is not None else 0
