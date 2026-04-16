from __future__ import annotations

import psycopg2.extensions
from typing import Any

from app.core.utils import utcnow_iso


def _row_to_message(row: tuple) -> dict[str, Any]:
    return {
        "id": row[0],
        "session_id": row[1],
        "sender": row[2],
        "original_text": row[3],
        "translated_text": row[4],
        "source_language": row[5],
        "target_language": row[6],
        "confidence": float(row[7]),
        "created_at": row[8],
    }


def create_message(
    conn: psycopg2.extensions.connection,
    *,
    session_id: str,
    sender: str,
    original_text: str,
    translated_text: str,
    source_language: str,
    target_language: str,
    confidence: float,
) -> dict[str, Any]:
    created_at = utcnow_iso()
    with conn.cursor() as cursor:
        cursor.execute(
            """
            INSERT INTO triage_messages (
                session_id, sender, original_text, translated_text,
                source_language, target_language, confidence, created_at
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING id, session_id, sender, original_text, translated_text,
                      source_language, target_language, confidence, created_at
            """,
            (
                session_id,
                sender,
                original_text,
                translated_text,
                source_language,
                target_language,
                confidence,
                created_at,
            ),
        )
        row = cursor.fetchone()
    conn.commit()
    assert row is not None
    return _row_to_message(row)


def list_by_session(conn: psycopg2.extensions.connection, session_id: str) -> list[dict[str, Any]]:
    with conn.cursor() as cursor:
        cursor.execute(
            """
            SELECT id, session_id, sender, original_text, translated_text,
                   source_language, target_language, confidence, created_at
            FROM triage_messages
            WHERE session_id = %s
            ORDER BY created_at ASC, id ASC
            """,
            (session_id,),
        )
        rows = cursor.fetchall()
    return [_row_to_message(row) for row in rows]


def average_confidence_for_session(conn: psycopg2.extensions.connection, session_id: str) -> float | None:
    with conn.cursor() as cursor:
        cursor.execute(
            "SELECT AVG(confidence) FROM triage_messages WHERE session_id = %s",
            (session_id,),
        )
        row = cursor.fetchone()
    if row is None or row[0] is None:
        return None
    return round(float(row[0]), 2)
