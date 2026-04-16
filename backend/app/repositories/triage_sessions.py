from __future__ import annotations

import psycopg2.extensions
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from app.core.utils import utcnow_iso

_SESSION_COLS = """
    id, patient_id, provider_id, status, started_at, ended_at, duration_seconds,
    patient_language, bp_systolic, bp_diastolic, heart_rate, temperature,
    respiratory_rate, spo2, ats_category, nurse_confirmed_ats, avg_translation_confidence,
    summary, summary_generated_at
"""


def _row_to_session(row: tuple) -> dict[str, Any]:
    return {
        "id": row[0],
        "patient_id": row[1],
        "provider_id": row[2],
        "status": row[3],
        "started_at": row[4],
        "ended_at": row[5],
        "duration_seconds": row[6],
        "patient_language": row[7],
        "bp_systolic": row[8],
        "bp_diastolic": row[9],
        "heart_rate": row[10],
        "temperature": float(row[11]) if row[11] is not None else None,
        "respiratory_rate": row[12],
        "spo2": row[13],
        "ats_category": row[14],
        "nurse_confirmed_ats": bool(row[15]),
        "avg_translation_confidence": float(row[16]) if row[16] is not None else None,
        "summary": row[17] if len(row) > 17 else None,
        "summary_generated_at": row[18] if len(row) > 18 else None,
    }


def get_by_id(conn: psycopg2.extensions.connection, session_id: str) -> dict[str, Any] | None:
    with conn.cursor() as cursor:
        cursor.execute(
            f"SELECT {_SESSION_COLS} FROM triage_sessions WHERE id = %s",
            (session_id,),
        )
        row = cursor.fetchone()
    return _row_to_session(row) if row else None


def get_active_for_patient(conn: psycopg2.extensions.connection, patient_id: str) -> dict[str, Any] | None:
    with conn.cursor() as cursor:
        cursor.execute(
            f"""
            SELECT {_SESSION_COLS} FROM triage_sessions
            WHERE patient_id = %s AND status = 'active'
            ORDER BY started_at DESC LIMIT 1
            """,
            (patient_id,),
        )
        row = cursor.fetchone()
    return _row_to_session(row) if row else None


def create_session(
    conn: psycopg2.extensions.connection,
    *,
    patient_id: str,
    provider_id: str | None,
    patient_language: str = "ar",
) -> dict[str, Any]:
    session_id = str(uuid4())
    started_at = utcnow_iso()
    with conn.cursor() as cursor:
        cursor.execute(
            f"""
            INSERT INTO triage_sessions (
                id, patient_id, provider_id, status, started_at, patient_language
            )
            VALUES (%s, %s, %s, 'active', %s, %s)
            RETURNING {_SESSION_COLS}
            """,
            (session_id, patient_id, provider_id, started_at, patient_language),
        )
        row = cursor.fetchone()
    conn.commit()
    assert row is not None
    return _row_to_session(row)


def update_session_fields(
    conn: psycopg2.extensions.connection,
    session_id: str,
    updates: dict[str, Any],
) -> dict[str, Any] | None:
    allowed = {
        "patient_language",
        "bp_systolic",
        "bp_diastolic",
        "heart_rate",
        "temperature",
        "respiratory_rate",
        "spo2",
        "ats_category",
        "nurse_confirmed_ats",
        "avg_translation_confidence",
    }
    fields: list[str] = []
    params: list[Any] = []

    for key, value in updates.items():
        if key not in allowed:
            continue
        fields.append(f"{key} = %s")
        params.append(value)

    if not fields:
        return get_by_id(conn, session_id)

    params.append(session_id)
    with conn.cursor() as cursor:
        cursor.execute(
            f"""
            UPDATE triage_sessions SET {", ".join(fields)}
            WHERE id = %s
            RETURNING {_SESSION_COLS}
            """,
            tuple(params),
        )
        row = cursor.fetchone()
    conn.commit()
    return _row_to_session(row) if row else None


def save_summary(
    conn: psycopg2.extensions.connection,
    session_id: str,
    summary: str,
) -> None:
    """Persist the generated summary so subsequent calls skip regeneration."""
    with conn.cursor() as cursor:
        cursor.execute(
            """
            UPDATE triage_sessions
            SET summary = %s, summary_generated_at = %s
            WHERE id = %s
            """,
            (summary, utcnow_iso(), session_id),
        )
    conn.commit()


def _parse_iso_utc(s: str) -> datetime:
    if s.endswith("Z"):
        s = s[:-1] + "+00:00"
    return datetime.fromisoformat(s)


def complete_session(
    conn: psycopg2.extensions.connection,
    session_id: str,
) -> dict[str, Any] | None:
    session = get_by_id(conn, session_id)
    if session is None or session["status"] != "active":
        return None
    ended_at = utcnow_iso()
    started = _parse_iso_utc(session["started_at"])
    ended = _parse_iso_utc(ended_at)
    if ended.tzinfo is None:
        ended = ended.replace(tzinfo=timezone.utc)
    if started.tzinfo is None:
        started = started.replace(tzinfo=timezone.utc)
    duration_seconds = max(0, int((ended - started).total_seconds()))

    with conn.cursor() as cursor:
        cursor.execute(
            f"""
            UPDATE triage_sessions
            SET status = 'completed', ended_at = %s, duration_seconds = %s
            WHERE id = %s AND status = 'active'
            RETURNING {_SESSION_COLS}
            """,
            (ended_at, duration_seconds, session_id),
        )
        row = cursor.fetchone()
    conn.commit()
    return _row_to_session(row) if row else None


def count_completed_history(
    conn: psycopg2.extensions.connection,
    *,
    search: str | None,
) -> int:
    base = """
        SELECT COUNT(*)
        FROM triage_sessions s
        JOIN patients p ON p.id = s.patient_id
        WHERE s.status = 'completed'
    """
    params: list[Any] = []
    if search and search.strip():
        pattern = f"%{search.strip()}%"
        base += " AND (p.full_name ILIKE %s OR p.mrn ILIKE %s OR p.id ILIKE %s)"
        params.extend([pattern, pattern, pattern])
    with conn.cursor() as cursor:
        cursor.execute(base, tuple(params))
        row = cursor.fetchone()
    return int(row[0]) if row and row[0] is not None else 0


def list_completed_history(
    conn: psycopg2.extensions.connection,
    *,
    search: str | None,
    limit: int,
    offset: int,
) -> list[dict[str, Any]]:
    base = """
        SELECT
            s.id, s.started_at, s.ended_at, s.duration_seconds, s.patient_language,
            s.ats_category, s.bp_systolic, s.bp_diastolic, s.heart_rate, s.temperature,
            s.respiratory_rate, s.spo2, s.avg_translation_confidence,
            p.id AS patient_id, p.mrn, p.full_name
        FROM triage_sessions s
        JOIN patients p ON p.id = s.patient_id
        WHERE s.status = 'completed'
    """
    params: list[Any] = []
    if search and search.strip():
        pattern = f"%{search.strip()}%"
        base += " AND (p.full_name ILIKE %s OR p.mrn ILIKE %s OR p.id ILIKE %s)"
        params.extend([pattern, pattern, pattern])
    base += " ORDER BY s.started_at DESC LIMIT %s OFFSET %s"
    params.extend([limit, offset])

    with conn.cursor() as cursor:
        cursor.execute(base, tuple(params))
        rows = cursor.fetchall()

    out: list[dict[str, Any]] = []
    for row in rows:
        out.append(
            {
                "session_id": row[0],
                "started_at": row[1],
                "ended_at": row[2],
                "duration_seconds": row[3],
                "patient_language": row[4],
                "ats_category": row[5],
                "bp_systolic": row[6],
                "bp_diastolic": row[7],
                "heart_rate": row[8],
                "temperature": float(row[9]) if row[9] is not None else None,
                "respiratory_rate": row[10],
                "spo2": row[11],
                "avg_translation_confidence": float(row[12]) if row[12] is not None else None,
                "patient_id": row[13],
                "mrn": row[14],
                "patient_name": row[15],
            }
        )
    return out
