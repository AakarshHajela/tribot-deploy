from __future__ import annotations

import psycopg2.extensions

from fastapi import APIRouter, Depends

from app.api.deps import get_current_clinician
from app.data.database import get_db
from app.schemas.translation import TranslateRequest, TranslateResponse
from app.services.translator import translate_and_log

router = APIRouter(prefix="/translate", tags=["translation"])


@router.post("", response_model=TranslateResponse)
def translate(
    payload: TranslateRequest,
    conn: psycopg2.extensions.connection = Depends(get_db),
    clinician: dict = Depends(get_current_clinician),
) -> TranslateResponse:
    result = translate_and_log(
        conn,
        source_text=payload.source_text,
        source_language=payload.source_language,
        target_language=payload.target_language,
        session_id=payload.session_id,
        clinician_id=clinician["id"],
    )
    return TranslateResponse(**result)
