from __future__ import annotations

import psycopg2.extensions
from typing import Any

from app.core.utils import utcnow_iso


def create_attempt(
    conn: psycopg2.extensions.connection,
    *,
    username: str,
    success: bool,
    reason: str,
    user_id: str | None = None,
    ip_address: str | None = None,
) -> dict[str, Any]:
    timestamp = utcnow_iso()
    with conn.cursor() as cursor:
        cursor.execute(
            '''
            INSERT INTO login_attempts (timestamp, user_id, username, success, reason, ip_address)
            VALUES (%s, %s, %s, %s, %s, %s)
            RETURNING id, timestamp, user_id, username, success, reason, ip_address
            ''',
            (
                timestamp,
                user_id,
                username,
                success,
                reason,
                ip_address,
            ),
        )
        row = cursor.fetchone()
    conn.commit()
    assert row is not None
    return {
        "id": row[0],
        "timestamp": row[1],
        "user_id": row[2],
        "username": row[3],
        "success": bool(row[4]),
        "reason": row[5],
        "ip_address": row[6],
    }
