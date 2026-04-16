from __future__ import annotations

import psycopg2.extensions

from app.repositories import patients as patients_repo
from app.repositories import triage_messages as messages_repo
from app.repositories import triage_sessions as sessions_repo


_DEMO_SESSION_MRN = "MRN-2024-001234"  # Ahmed Al-Mansoori


_MESSAGES = [
    {
        "sender": "clinician",
        "original_text": "Hello, can you describe your symptoms?",
        "translated_text": "مرحبًا، هل يمكنك وصف الأعراض الخاصة بك؟",
        "source_language": "en",
        "target_language": "ar",
        "confidence": 96.0,
    },
    {
        "sender": "patient",
        "original_text": "ألم في الصدر وضيق في التنفس",
        "translated_text": "Chest pain and shortness of breath",
        "source_language": "ar",
        "target_language": "en",
        "confidence": 94.0,
    },
    {
        "sender": "clinician",
        "original_text": "When did the chest pain start?",
        "translated_text": "متى بدأ ألم الصدر؟",
        "source_language": "en",
        "target_language": "ar",
        "confidence": 95.0,
    },
    {
        "sender": "patient",
        "original_text": "منذ حوالي ساعة",
        "translated_text": "About an hour ago",
        "source_language": "ar",
        "target_language": "en",
        "confidence": 92.0,
    },
    {
        "sender": "clinician",
        "original_text": "Is the pain spreading to your arm or jaw?",
        "translated_text": "هل ينتشر الألم إلى ذراعك أو فكك؟",
        "source_language": "en",
        "target_language": "ar",
        "confidence": 93.0,
    },
    {
        "sender": "patient",
        "original_text": "نعم، ينتشر إلى الذراع اليسرى",
        "translated_text": "Yes, it spreads to the left arm",
        "source_language": "ar",
        "target_language": "en",
        "confidence": 91.0,
    },
    {
        "sender": "clinician",
        "original_text": "Do you have any history of heart disease?",
        "translated_text": "هل لديك تاريخ مرضي بأمراض القلب؟",
        "source_language": "en",
        "target_language": "ar",
        "confidence": 94.0,
    },
    {
        "sender": "patient",
        "original_text": "لا، لكن لدي ضغط دم مرتفع",
        "translated_text": "No, but I have high blood pressure",
        "source_language": "ar",
        "target_language": "en",
        "confidence": 93.0,
    },
]


def seed_demo_triage_session(conn: psycopg2.extensions.connection) -> None:
    """
    Insert one completed triage session for Ahmed Al-Mansoori if none exists yet.
    Safe to call on every startup (idempotent).
    """
    patient = patients_repo.ensure_patient(
        conn,
        mrn=_DEMO_SESSION_MRN,
        full_name="Ahmed Al-Mansoori",
        patient_language="ar",
    )

    # Only seed once — skip if the patient already has a completed session
    with conn.cursor() as cursor:
        cursor.execute(
            "SELECT id FROM triage_sessions WHERE patient_id = %s AND status = 'completed' LIMIT 1",
            (patient["id"],),
        )
        if cursor.fetchone() is not None:
            return

    # Create and immediately complete the session
    session = sessions_repo.create_session(
        conn,
        patient_id=patient["id"],
        provider_id=None,
        patient_language="ar",
    )
    session_id = session["id"]

    # Insert messages
    for msg in _MESSAGES:
        messages_repo.create_message(conn, session_id=session_id, **msg)

    # Set vitals and ATS
    sessions_repo.update_session_fields(
        conn,
        session_id,
        {
            "bp_systolic": 120,
            "bp_diastolic": 80,
            "heart_rate": 75,
            "temperature": 98.6,
            "respiratory_rate": 16,
            "spo2": 98,
            "ats_category": 2,
            "nurse_confirmed_ats": True,
            "avg_translation_confidence": 93.5,
        },
    )

    # Mark as completed
    sessions_repo.complete_session(conn, session_id)
