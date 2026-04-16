from __future__ import annotations

import psycopg2.extensions
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import Response

from app.api.deps import get_current_clinician
from app.core.errors import BadRequestError
from app.data.database import get_db
from app.repositories import patients as patients_repo
from app.repositories import triage_messages as messages_repo
from app.repositories import triage_sessions as sessions_repo
from app.repositories.translation_logs import list_logs
from app.schemas.logs import TranslationLogListResponse, TranslationLogResponse
from app.schemas.triage import (
    CreateTriageSessionRequest,
    HistoryListResponse,
    HistoryRowResponse,
    PatchTriageSessionRequest,
    PatientSearchResult,
    SendTriageMessageRequest,
    SessionSummaryResponse,
    SubmitSessionResponse,
    TriageMessageResponse,
    TriageSessionDetailResponse,
    TriageSessionResponse,
    VitalsSnapshot,
)
from app.services.translator import translate_and_log

router = APIRouter(prefix="/triage", tags=["triage"])


def _session_to_response(row: dict) -> TriageSessionResponse:
    return TriageSessionResponse(
        id=row["id"],
        patient_id=row["patient_id"],
        provider_id=row["provider_id"],
        status=row["status"],
        started_at=row["started_at"],
        ended_at=row["ended_at"],
        duration_seconds=row["duration_seconds"],
        patient_language=row["patient_language"],
        vitals=VitalsSnapshot(
            bp_systolic=row["bp_systolic"],
            bp_diastolic=row["bp_diastolic"],
            heart_rate=row["heart_rate"],
            temperature=row["temperature"],
            respiratory_rate=row["respiratory_rate"],
            spo2=row["spo2"],
        ),
        ats_category=row["ats_category"],
        nurse_confirmed_ats=row["nurse_confirmed_ats"],
        avg_translation_confidence=row["avg_translation_confidence"],
    )


@router.post("/sessions", response_model=TriageSessionResponse, status_code=201)
def create_triage_session(
    payload: CreateTriageSessionRequest,
    conn: psycopg2.extensions.connection = Depends(get_db),
    clinician: dict = Depends(get_current_clinician),
) -> TriageSessionResponse:
    patient = patients_repo.get_by_id(conn, payload.patient_id)
    if patient is None:
        raise HTTPException(status_code=404, detail="Patient not found.")

    existing = sessions_repo.get_active_for_patient(conn, payload.patient_id)
    if existing is not None:
        raise HTTPException(
            status_code=409,
            detail={
                "message": "An active triage session already exists for this patient.",
                "session_id": existing["id"],
            },
        )

    raw_provider = (payload.provider_id or "").strip()
    provider_id: str | None = raw_provider if (raw_provider and raw_provider.upper() != "NA") else clinician["id"]

    row = sessions_repo.create_session(
        conn,
        patient_id=payload.patient_id,
        provider_id=provider_id,
        patient_language=payload.patient_language or patient["patient_language"],
    )
    return _session_to_response(row)


@router.get("/sessions/active", response_model=TriageSessionResponse)
def get_active_session(
    patient_id: str = Query(..., description="Patient UUID"),
    conn: psycopg2.extensions.connection = Depends(get_db),
    clinician: dict = Depends(get_current_clinician),
) -> TriageSessionResponse:
    row = sessions_repo.get_active_for_patient(conn, patient_id)
    if row is None:
        raise HTTPException(status_code=404, detail="No active session for this patient.")
    return _session_to_response(row)


def _load_session_detail(
    conn: psycopg2.extensions.connection,
    session_id: str,
) -> tuple[dict, dict, list[dict], str, bool]:
    """
    Fetch session, patient, messages, and summary for a session_id.
    Generates and caches the summary in the DB if not already present.
    Returns (session, patient, messages, summary, ai_was_used).
    """
    from app.services.summary import generate_summary
    from app.core.config import get_settings

    session = sessions_repo.get_by_id(conn, session_id)
    if session is None:
        raise HTTPException(status_code=404, detail="Session not found.")

    patient = patients_repo.get_by_id(conn, session["patient_id"])
    if patient is None:
        raise HTTPException(status_code=404, detail="Patient not found.")

    messages = messages_repo.list_by_session(conn, session_id)

    cached = (session.get("summary") or "").strip()
    if cached:
        # Already cached — flag reflects settings so callers know if AI is on
        settings = get_settings()
        return session, patient, messages, cached, settings.ai_summary_enabled

    settings = get_settings()
    summary, ai_was_used = generate_summary(
        session,
        patient,
        messages,
        model_path=settings.summary_model_path,
        use_ai=settings.ai_summary_enabled,
    )
    sessions_repo.save_summary(conn, session_id, summary)
    return session, patient, messages, summary, ai_was_used


@router.get("/sessions/{session_id}", response_model=TriageSessionDetailResponse)
def get_triage_session(
    session_id: str,
    conn: psycopg2.extensions.connection = Depends(get_db),
    clinician: dict = Depends(get_current_clinician),
) -> TriageSessionDetailResponse:
    session, patient, messages, summary, _ = _load_session_detail(conn, session_id)
    return TriageSessionDetailResponse(
        session=_session_to_response(session),
        patient=PatientSearchResult(**patient),
        messages=[TriageMessageResponse(**m) for m in messages],
        summary=summary,
    )


@router.patch("/sessions/{session_id}", response_model=TriageSessionResponse)
def patch_triage_session(
    session_id: str,
    payload: PatchTriageSessionRequest,
    conn: psycopg2.extensions.connection = Depends(get_db),
    clinician: dict = Depends(get_current_clinician),
) -> TriageSessionResponse:
    session = sessions_repo.get_by_id(conn, session_id)
    if session is None:
        raise HTTPException(status_code=404, detail="Session not found.")
    if session["status"] != "active":
        raise BadRequestError("Cannot update a completed session.")

    data = payload.model_dump(exclude_unset=True)
    updated = sessions_repo.update_session_fields(conn, session_id, data)
    assert updated is not None
    return _session_to_response(updated)


@router.post("/sessions/{session_id}/messages", response_model=TriageMessageResponse, status_code=201)
def post_triage_message(
    session_id: str,
    payload: SendTriageMessageRequest,
    conn: psycopg2.extensions.connection = Depends(get_db),
    clinician: dict = Depends(get_current_clinician),
) -> TriageMessageResponse:
    session = sessions_repo.get_by_id(conn, session_id)
    if session is None:
        raise HTTPException(status_code=404, detail="Session not found.")
    if session["status"] != "active":
        raise BadRequestError("Cannot add messages to a completed session.")

    if payload.translated_text is not None and payload.confidence is not None:
        translated = payload.translated_text.strip()
        confidence = float(payload.confidence)
    else:
        result = translate_and_log(
            conn,
            source_text=payload.original_text,
            source_language=payload.source_language,
            target_language=payload.target_language,
            session_id=session_id,
            clinician_id=clinician["id"],
        )
        translated = result["translated_text"]
        confidence = float(result["confidence_score"])

    msg = messages_repo.create_message(
        conn,
        session_id=session_id,
        sender=payload.sender,
        original_text=payload.original_text,
        translated_text=translated,
        source_language=payload.source_language.strip().lower(),
        target_language=payload.target_language.strip().lower(),
        confidence=confidence,
    )
    avg = messages_repo.average_confidence_for_session(conn, session_id)
    if avg is not None:
        sessions_repo.update_session_fields(conn, session_id, {"avg_translation_confidence": avg})
    return TriageMessageResponse(**msg)


def _vitals_complete(row: dict) -> bool:
    return (
        row.get("bp_systolic") is not None
        and row.get("bp_diastolic") is not None
        and row.get("heart_rate") is not None
        and row.get("temperature") is not None
        and row.get("respiratory_rate") is not None
        and row.get("spo2") is not None
    )


@router.post("/sessions/{session_id}/submit", response_model=SubmitSessionResponse)
def submit_triage_session(
    session_id: str,
    conn: psycopg2.extensions.connection = Depends(get_db),
    clinician: dict = Depends(get_current_clinician),
) -> SubmitSessionResponse:
    session = sessions_repo.get_by_id(conn, session_id)
    if session is None:
        raise HTTPException(status_code=404, detail="Session not found.")
    if session["status"] != "active":
        raise BadRequestError("Session is already submitted.")

    if session.get("ats_category") is None:
        raise BadRequestError("Select an ATS category before submitting.")
    if not _vitals_complete(session):
        raise BadRequestError("Enter all vitals before submitting.")

    completed = sessions_repo.complete_session(conn, session_id)
    if completed is None:
        raise BadRequestError("Could not complete session.")

    patient = patients_repo.get_by_id(conn, completed["patient_id"])
    name = patient["full_name"] if patient else "Patient"
    cat = completed.get("ats_category")
    return SubmitSessionResponse(
        session=_session_to_response(completed),
        patient_name=name,
        message=f"ATS Cat {cat} assigned to {name}. Transcript logged.",
    )


@router.get("/sessions/{session_id}/logs", response_model=TranslationLogListResponse)
def get_session_translation_logs(
    session_id: str,
    conn: psycopg2.extensions.connection = Depends(get_db),
    clinician: dict = Depends(get_current_clinician),
) -> TranslationLogListResponse:
    session = sessions_repo.get_by_id(conn, session_id)
    if session is None:
        raise HTTPException(status_code=404, detail="Session not found.")
    items = list_logs(conn, session_id=session_id, limit=500)
    return TranslationLogListResponse(
        count=len(items),
        items=[TranslationLogResponse(**item) for item in items],
    )


@router.get("/sessions/{session_id}/summary", response_model=SessionSummaryResponse)
def get_session_summary(
    session_id: str,
    conn: psycopg2.extensions.connection = Depends(get_db),
) -> SessionSummaryResponse:
    session, patient, _, summary, ai_was_used = _load_session_detail(conn, session_id)
    return SessionSummaryResponse(
        session_id=session_id,
        patient_name=patient.get("full_name", "Unknown"),
        summary=summary,
        ai_generated=ai_was_used,
    )


@router.get("/history", response_model=HistoryListResponse)
def list_session_history(
    q: str | None = Query(default=None, description="Filter by patient name, MRN, or patient id."),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    conn: psycopg2.extensions.connection = Depends(get_db),
    clinician: dict = Depends(get_current_clinician),
) -> HistoryListResponse:
    total = sessions_repo.count_completed_history(conn, search=q)
    rows = sessions_repo.list_completed_history(conn, search=q, limit=limit, offset=offset)
    return HistoryListResponse(
        total=total,
        items=[HistoryRowResponse(**r) for r in rows],
    )


@router.get("/sessions/{session_id}/export.pdf")
def export_session_pdf(
    session_id: str,
    conn: psycopg2.extensions.connection = Depends(get_db),
) -> Response:
    from app.services.pdf import generate_session_pdf

    session, patient, messages, summary, _ = _load_session_detail(conn, session_id)

    pdf_bytes = generate_session_pdf(session, patient, messages, summary=summary)

    patient_name = patient.get("full_name", "patient").replace(" ", "_")
    filename = f"TRIBOT_{patient_name}_{session_id[:8]}.pdf"

    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
