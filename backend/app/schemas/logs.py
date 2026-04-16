from __future__ import annotations

from pydantic import BaseModel


class TranslationLogResponse(BaseModel):
    id: int
    session_id: str
    timestamp: str
    source_text: str
    source_language: str
    target_language: str
    translated_output: str
    confidence_score: float
    escalation_flag: bool
    escalation_reason: str | None = None
    latency_ms: int
    model_name: str
    clinician_id: str | None = None


class TranslationLogListResponse(BaseModel):
    count: int
    items: list[TranslationLogResponse]
