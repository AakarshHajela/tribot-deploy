from __future__ import annotations

import psycopg2.extensions
from typing import Any

from app.core.utils import utcnow_iso


def _row_to_log(row: tuple) -> dict[str, Any]:
    return {
        "id": row[0],
        "session_id": row[1],
        "timestamp": row[2],
        "source_text": row[3],
        "source_language": row[4],
        "target_language": row[5],
        "translated_output": row[6],
        "confidence_score": row[7],
        "escalation_flag": bool(row[8]),
        "escalation_reason": row[9],
        "latency_ms": row[10],
        "model_name": row[11],
        "clinician_id": row[12],
    }


def create_log(
    conn: psycopg2.extensions.connection,
    *,
    session_id: str,
    source_text: str,
    source_language: str,
    target_language: str,
    translated_output: str,
    confidence_score: float,
    escalation_flag: bool,
    escalation_reason: str | None,
    latency_ms: int,
    model_name: str,
    clinician_id: str | None,
) -> dict[str, Any]:
    timestamp = utcnow_iso()
    with conn.cursor() as cursor:
        cursor.execute(
            '''
            INSERT INTO translation_logs (
                session_id,
                timestamp,
                source_text,
                source_language,
                target_language,
                translated_output,
                confidence_score,
                escalation_flag,
                escalation_reason,
                latency_ms,
                model_name,
                clinician_id
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING id, session_id, timestamp, source_text, source_language, target_language,
                      translated_output, confidence_score, escalation_flag, escalation_reason,
                      latency_ms, model_name, clinician_id
            ''',
            (
                session_id,
                timestamp,
                source_text,
                source_language,
                target_language,
                translated_output,
                confidence_score,
                escalation_flag,
                escalation_reason,
                latency_ms,
                model_name,
                clinician_id,
            ),
        )
        row = cursor.fetchone()
    conn.commit()
    assert row is not None
    return _row_to_log(row)


def list_logs(
    conn: psycopg2.extensions.connection,
    *,
    session_id: str | None = None,
    start_at: str | None = None,
    end_at: str | None = None,
    escalation_flag: bool | None = None,
    limit: int = 100,
) -> list[dict[str, Any]]:
    query = "SELECT id, session_id, timestamp, source_text, source_language, target_language, translated_output, confidence_score, escalation_flag, escalation_reason, latency_ms, model_name, clinician_id FROM translation_logs WHERE TRUE"
    params: list[Any] = []

    if session_id:
        query += " AND session_id = %s"
        params.append(session_id)
    if start_at:
        query += " AND timestamp >= %s"
        params.append(start_at)
    if end_at:
        query += " AND timestamp <= %s"
        params.append(end_at)
    if escalation_flag is not None:
        query += " AND escalation_flag = %s"
        params.append(escalation_flag)

    query += " ORDER BY timestamp DESC LIMIT %s"
    params.append(limit)

    with conn.cursor() as cursor:
        cursor.execute(query, tuple(params))
        rows = cursor.fetchall()
    return [_row_to_log(row) for row in rows]
