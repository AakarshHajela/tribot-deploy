from __future__ import annotations

from pydantic import BaseModel, field_validator


class TranslateRequest(BaseModel):
    source_text: str
    source_language: str
    target_language: str
    session_id: str | None = None

    @field_validator("source_text")
    @classmethod
    def validate_text(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("source_text cannot be empty.")
        return cleaned

    @field_validator("source_language", "target_language")
    @classmethod
    def validate_language(cls, value: str) -> str:
        cleaned = value.strip().lower()
        if not cleaned:
            raise ValueError("Language cannot be empty.")
        return cleaned


class TranslateResponse(BaseModel):
    session_id: str
    timestamp: str
    translated_text: str
    confidence_score: float
    escalation_flag: bool
    escalation_reason: str | None = None
    model_name: str


class HealthResponse(BaseModel):
    status: str
    app_name: str
    version: str
