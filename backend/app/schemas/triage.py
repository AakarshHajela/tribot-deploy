from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field, field_validator, model_validator


class PatientSearchResult(BaseModel):
    id: str
    mrn: str
    full_name: str
    patient_language: str
    created_at: str


class PatientSearchResponse(BaseModel):
    items: list[PatientSearchResult]


class CreateTriageSessionRequest(BaseModel):
    patient_id: str = Field(..., min_length=1)
    patient_language: str | None = Field(
        default=None,
        description="Override patient language for this session. Defaults to the patient's own language.",
    )
    provider_id: str | None = None


class VitalsSnapshot(BaseModel):
    bp_systolic: int | None = None
    bp_diastolic: int | None = None
    heart_rate: int | None = None
    temperature: float | None = None
    respiratory_rate: int | None = None
    spo2: int | None = None


class TriageSessionResponse(BaseModel):
    id: str
    patient_id: str
    provider_id: str | None = None
    status: str
    started_at: str
    ended_at: str | None = None
    duration_seconds: int | None = None
    patient_language: str
    vitals: VitalsSnapshot
    ats_category: int | None = None
    nurse_confirmed_ats: bool = False
    avg_translation_confidence: float | None = None


class PatchTriageSessionRequest(BaseModel):
    patient_language: str | None = None
    bp_systolic: int | None = None
    bp_diastolic: int | None = None
    heart_rate: int | None = None
    temperature: float | None = None
    respiratory_rate: int | None = None
    spo2: int | None = None
    ats_category: int | None = Field(default=None, ge=1, le=5)
    nurse_confirmed_ats: bool | None = None

    @field_validator("patient_language")
    @classmethod
    def normalize_lang(cls, value: str | None) -> str | None:
        if value is None:
            return None
        v = value.strip().lower()
        if v in {"english", "en"}:
            return "en"
        if v in {"arabic", "ar"}:
            return "ar"
        return v


class TriageMessageResponse(BaseModel):
    id: int
    session_id: str
    sender: str
    original_text: str
    translated_text: str
    source_language: str
    target_language: str
    confidence: float
    created_at: str


class SendTriageMessageRequest(BaseModel):
    sender: Literal["clinician", "patient"]
    original_text: str
    source_language: str
    target_language: str
    translated_text: str | None = None
    confidence: float | None = Field(default=None, ge=0, le=100)

    @field_validator("original_text")
    @classmethod
    def strip_text(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("original_text cannot be empty.")
        return cleaned

    @model_validator(mode="after")
    def translated_and_confidence_together(self) -> SendTriageMessageRequest:
        has_t = self.translated_text is not None and str(self.translated_text).strip() != ""
        has_c = self.confidence is not None
        if has_t != has_c:
            raise ValueError("Provide both translated_text and confidence, or neither (server translates).")
        return self


class TriageSessionDetailResponse(BaseModel):
    session: TriageSessionResponse
    patient: PatientSearchResult
    messages: list[TriageMessageResponse]
    summary: str | None = None


class HistoryRowResponse(BaseModel):
    session_id: str
    started_at: str
    ended_at: str | None = None
    duration_seconds: int | None = None
    patient_language: str
    ats_category: int | None = None
    patient_id: str
    mrn: str
    patient_name: str
    bp_systolic: int | None = None
    bp_diastolic: int | None = None
    heart_rate: int | None = None
    temperature: float | None = None
    respiratory_rate: int | None = None
    spo2: int | None = None
    avg_translation_confidence: float | None = None


class HistoryListResponse(BaseModel):
    total: int
    items: list[HistoryRowResponse]


class SubmitSessionResponse(BaseModel):
    session: TriageSessionResponse
    patient_name: str
    message: str


class SessionSummaryResponse(BaseModel):
    session_id: str
    patient_name: str
    summary: str
    ai_generated: bool
