from __future__ import annotations

import psycopg2.extensions
from typing import Any
from uuid import uuid4

from app.core.utils import utcnow_iso

_SELECT = "SELECT id, mrn, full_name, patient_language, created_at FROM patients"


def _row_to_patient(row: tuple) -> dict[str, Any]:
    return {
        "id": row[0],
        "mrn": row[1],
        "full_name": row[2],
        "patient_language": row[3],
        "created_at": row[4],
    }


def _normalize_language(value: str) -> str:
    v = value.strip().lower()
    if v in {"english", "en"}:
        return "en"
    if v in {"arabic", "ar"}:
        return "ar"
    return v


def get_by_id(conn: psycopg2.extensions.connection, patient_id: str) -> dict[str, Any] | None:
    with conn.cursor() as cursor:
        cursor.execute(f"{_SELECT} WHERE id = %s", (patient_id,))
        row = cursor.fetchone()
    return _row_to_patient(row) if row else None


def search(conn: psycopg2.extensions.connection, *, query: str, limit: int = 50) -> list[dict[str, Any]]:
    q = query.strip()
    if not q:
        return []
    pattern = f"%{q}%"
    with conn.cursor() as cursor:
        cursor.execute(
            f"""
            {_SELECT}
            WHERE mrn ILIKE %s OR full_name ILIKE %s OR id ILIKE %s
            ORDER BY full_name ASC
            LIMIT %s
            """,
            (pattern, pattern, pattern, limit),
        )
        rows = cursor.fetchall()
    return [_row_to_patient(row) for row in rows]


def create_patient(
    conn: psycopg2.extensions.connection,
    *,
    mrn: str,
    full_name: str,
    patient_language: str = "ar",
    patient_id: str | None = None,
) -> dict[str, Any]:
    pid = patient_id or str(uuid4())
    created_at = utcnow_iso()
    lang = _normalize_language(patient_language)
    with conn.cursor() as cursor:
        cursor.execute(
            """
            INSERT INTO patients (id, mrn, full_name, patient_language, created_at)
            VALUES (%s, %s, %s, %s, %s)
            RETURNING id, mrn, full_name, patient_language, created_at
            """,
            (pid, mrn.strip(), full_name.strip(), lang, created_at),
        )
        row = cursor.fetchone()
    conn.commit()
    assert row is not None
    return _row_to_patient(row)


def update_patient(
    conn: psycopg2.extensions.connection,
    patient_id: str,
    *,
    mrn: str | None = None,
    full_name: str | None = None,
    patient_language: str | None = None,
) -> dict[str, Any] | None:
    fields: list[str] = []
    params: list[Any] = []
    if mrn is not None:
        fields.append("mrn = %s")
        params.append(mrn.strip())
    if full_name is not None:
        fields.append("full_name = %s")
        params.append(full_name.strip())
    if patient_language is not None:
        fields.append("patient_language = %s")
        params.append(_normalize_language(patient_language))
    if not fields:
        return get_by_id(conn, patient_id)
    params.append(patient_id)
    with conn.cursor() as cursor:
        cursor.execute(
            f"""
            UPDATE patients SET {", ".join(fields)}
            WHERE id = %s
            RETURNING id, mrn, full_name, patient_language, created_at
            """,
            tuple(params),
        )
        row = cursor.fetchone()
    conn.commit()
    return _row_to_patient(row) if row else None


def delete_patient(conn: psycopg2.extensions.connection, patient_id: str) -> bool:
    with conn.cursor() as cursor:
        cursor.execute("DELETE FROM patients WHERE id = %s", (patient_id,))
        deleted = cursor.rowcount
    conn.commit()
    return deleted > 0


def list_all(
    conn: psycopg2.extensions.connection,
    *,
    limit: int = 100,
    offset: int = 0,
) -> list[dict[str, Any]]:
    with conn.cursor() as cursor:
        cursor.execute(
            f"{_SELECT} ORDER BY full_name ASC LIMIT %s OFFSET %s",
            (limit, offset),
        )
        rows = cursor.fetchall()
    return [_row_to_patient(row) for row in rows]


def count_all(conn: psycopg2.extensions.connection) -> int:
    with conn.cursor() as cursor:
        cursor.execute("SELECT COUNT(*) FROM patients")
        row = cursor.fetchone()
    return int(row[0]) if row and row[0] is not None else 0


def ensure_patient(
    conn: psycopg2.extensions.connection,
    *,
    mrn: str,
    full_name: str,
    patient_language: str = "ar",
) -> dict[str, Any]:
    with conn.cursor() as cursor:
        cursor.execute(f"{_SELECT} WHERE mrn = %s", (mrn.strip(),))
        row = cursor.fetchone()
    if row:
        return _row_to_patient(row)
    return create_patient(conn, mrn=mrn, full_name=full_name, patient_language=patient_language)


def ensure_demo_patients(conn: psycopg2.extensions.connection) -> None:
    for mrn, full_name, lang in (
        ("MRN-2024-001234", "Ahmed Al-Mansoori", "ar"),
        ("MRN-2024-005678", "Maria Garcia", "en"),
    ):
        ensure_patient(conn, mrn=mrn, full_name=full_name, patient_language=lang)
