from __future__ import annotations

import psycopg2.extensions
from datetime import datetime

from fastapi import APIRouter, Depends, Query

from app.api.deps import get_current_clinician
from app.data.database import get_db
from app.repositories.translation_logs import list_logs
from app.schemas.logs import TranslationLogListResponse, TranslationLogResponse

router = APIRouter(prefix="/logs", tags=["audit-logs"])


def _fmt(dt: datetime | None) -> str | None:
    return dt.isoformat() if dt else None


@router.get("", response_model=TranslationLogListResponse)
def get_escalation_logs(
    escalation_only: bool = Query(
        default=True,
        description="When true (default) returns only flagged translations — "
                    "red-flag terms detected or confidence below threshold.",
    ),
    start_at: datetime | None = Query(default=None, description="Filter from this UTC timestamp."),
    end_at:   datetime | None = Query(default=None, description="Filter up to this UTC timestamp."),
    limit: int = Query(default=100, ge=1, le=500),
    conn: psycopg2.extensions.connection = Depends(get_db),
    clinician: dict = Depends(get_current_clinician),
) -> TranslationLogListResponse:
    """
    Admin / backend audit endpoint.

    By default returns only **escalation-flagged** translations across all sessions
    (red-flag medical terms detected, or confidence below threshold).
    Set `escalation_only=false` to see every translation log regardless of flag.

    For per-session logs use:  GET /api/v1/triage/sessions/{session_id}/logs
    """
    items = list_logs(
        conn,
        escalation_flag=True if escalation_only else None,
        start_at=_fmt(start_at),
        end_at=_fmt(end_at),
        limit=limit,
    )
    return TranslationLogListResponse(
        count=len(items),
        items=[TranslationLogResponse(**item) for item in items],
    )
