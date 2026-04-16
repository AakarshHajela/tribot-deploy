from __future__ import annotations

import psycopg2.extensions
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field

from app.api.deps import get_current_clinician
from app.core.errors import ConflictError
from app.data.database import get_db
from app.repositories import patients as patients_repo
from app.schemas.triage import PatientSearchResponse, PatientSearchResult

router = APIRouter(prefix="/patients", tags=["patients"])


class CreatePatientRequest(BaseModel):
    mrn: str = Field(..., min_length=1)
    full_name: str = Field(..., min_length=1)
    patient_language: str = Field(default="ar", description="Primary language of the patient: 'en' or 'ar'.")


class UpdatePatientRequest(BaseModel):
    mrn: str | None = Field(default=None, min_length=1)
    full_name: str | None = Field(default=None, min_length=1)
    patient_language: str | None = Field(default=None, description="Primary language of the patient: 'en' or 'ar'.")


class PatientListResponse(BaseModel):
    total: int
    items: list[PatientSearchResult]


@router.get("", response_model=PatientListResponse)
def list_patients(
    limit: int = Query(default=100, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    conn: psycopg2.extensions.connection = Depends(get_db),
    clinician: dict = Depends(get_current_clinician),
) -> PatientListResponse:
    total = patients_repo.count_all(conn)
    rows = patients_repo.list_all(conn, limit=limit, offset=offset)
    return PatientListResponse(total=total, items=[PatientSearchResult(**r) for r in rows])


@router.get("/search", response_model=PatientSearchResponse)
def search_patients(
    q: str = Query(..., min_length=1, description="Patient ID, MRN, or name substring."),
    limit: int = Query(default=50, ge=1, le=100),
    conn: psycopg2.extensions.connection = Depends(get_db),
    clinician: dict = Depends(get_current_clinician),
) -> PatientSearchResponse:
    rows = patients_repo.search(conn, query=q, limit=limit)
    return PatientSearchResponse(items=[PatientSearchResult(**r) for r in rows])


@router.get("/{patient_id}", response_model=PatientSearchResult)
def get_patient(
    patient_id: str,
    conn: psycopg2.extensions.connection = Depends(get_db),
    clinician: dict = Depends(get_current_clinician),
) -> PatientSearchResult:
    row = patients_repo.get_by_id(conn, patient_id)
    if row is None:
        raise HTTPException(status_code=404, detail="Patient not found.")
    return PatientSearchResult(**row)


@router.post("", response_model=PatientSearchResult, status_code=201)
def create_patient(
    payload: CreatePatientRequest,
    conn: psycopg2.extensions.connection = Depends(get_db),
    clinician: dict = Depends(get_current_clinician),
) -> PatientSearchResult:
    existing = patients_repo.search(conn, query=payload.mrn.strip(), limit=1)
    if any(p["mrn"].lower() == payload.mrn.strip().lower() for p in existing):
        raise ConflictError(f"A patient with MRN '{payload.mrn}' already exists.")
    row = patients_repo.create_patient(conn, mrn=payload.mrn, full_name=payload.full_name, patient_language=payload.patient_language)
    return PatientSearchResult(**row)


@router.patch("/{patient_id}", response_model=PatientSearchResult)
def update_patient(
    patient_id: str,
    payload: UpdatePatientRequest,
    conn: psycopg2.extensions.connection = Depends(get_db),
    clinician: dict = Depends(get_current_clinician),
) -> PatientSearchResult:
    existing = patients_repo.get_by_id(conn, patient_id)
    if existing is None:
        raise HTTPException(status_code=404, detail="Patient not found.")
    updated = patients_repo.update_patient(
        conn,
        patient_id,
        mrn=payload.mrn,
        full_name=payload.full_name,
        patient_language=payload.patient_language,
    )
    assert updated is not None
    return PatientSearchResult(**updated)


@router.delete("/{patient_id}", status_code=204)
def delete_patient(
    patient_id: str,
    conn: psycopg2.extensions.connection = Depends(get_db),
    clinician: dict = Depends(get_current_clinician),
) -> None:
    found = patients_repo.delete_patient(conn, patient_id)
    if not found:
        raise HTTPException(status_code=404, detail="Patient not found.")
