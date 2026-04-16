"""Shared fixtures for all API tests.

Strategy
--------
- ``get_db`` is overridden so no real PostgreSQL connection is needed.
- Repository functions are patched per-test with ``unittest.mock.patch``.
- ``get_by_username`` (used by JWT auth in deps.py) is patched for the whole
  session so Bearer tokens generated from test users are accepted everywhere.
"""
from __future__ import annotations

import pytest
from unittest.mock import MagicMock, patch
from fastapi.testclient import TestClient

from app.core.security import create_access_token, hash_password
from app.data.database import get_db

# ── Canonical test users ──────────────────────────────────────────────────────

ADMIN_PASSWORD = "AdminPass123!"
CLINICIAN_PASSWORD = "ClinicPass123!"
INACTIVE_PASSWORD = "InactivePass123!"

ADMIN_USER: dict = {
    "id": "admin-uuid-001",
    "username": "admin@hospital.au",
    "full_name": "Test Admin",
    "password_hash": hash_password(ADMIN_PASSWORD),
    "role": "admin",
    "is_active": True,
    "created_at": "2024-01-01T00:00:00Z",
}

CLINICIAN_USER: dict = {
    "id": "clinic-uuid-001",
    "username": "doc@hospital.au",
    "full_name": "Test Clinician",
    "password_hash": hash_password(CLINICIAN_PASSWORD),
    "role": "clinician",
    "is_active": True,
    "created_at": "2024-01-01T00:00:00Z",
}

INACTIVE_USER: dict = {
    "id": "inactive-uuid-001",
    "username": "inactive@hospital.au",
    "full_name": "Inactive User",
    "password_hash": hash_password(INACTIVE_PASSWORD),
    "role": "clinician",
    "is_active": False,
    "created_at": "2024-01-01T00:00:00Z",
}

USER_DB: dict[str, dict] = {
    u["username"]: u for u in [ADMIN_USER, CLINICIAN_USER, INACTIVE_USER]
}

# ── Shared mock objects ───────────────────────────────────────────────────────

MOCK_CONN = MagicMock()

MOCK_PATIENT: dict = {
    "id": "patient-uuid-001",
    "mrn": "MRN-2024-0001",
    "full_name": "Ahmed Al-Mansoori",
    "patient_language": "ar",
    "created_at": "2024-01-01T00:00:00Z",
}

MOCK_SESSION_ROW: dict = {
    "session_id": "session-uuid-001",
    "started_at": "2024-03-24T09:15:00Z",
    "ended_at": "2024-03-24T09:27:34Z",
    "duration_seconds": 754,
    "patient_language": "ar",
    "ats_category": 2,
    "bp_systolic": 120,
    "bp_diastolic": 80,
    "heart_rate": 72,
    "temperature": 36.5,
    "respiratory_rate": 16,
    "spo2": 98,
    "avg_translation_confidence": 0.91,
    "patient_id": MOCK_PATIENT["id"],
    "mrn": MOCK_PATIENT["mrn"],
    "patient_name": MOCK_PATIENT["full_name"],
}

MOCK_AUDIT_LOG: dict = {
    "id": 1,
    "timestamp": "2024-03-24T10:32:00Z",
    "admin_id": ADMIN_USER["id"],
    "admin_username": ADMIN_USER["username"],
    "action_type": "user_created",
    "target_user_id": CLINICIAN_USER["id"],
    "target_name": CLINICIAN_USER["full_name"],
    "details": "New Clinician account created.",
}

# ── Helpers ───────────────────────────────────────────────────────────────────

def bearer(user: dict) -> dict[str, str]:
    token, _ = create_access_token(user["username"])
    return {"Authorization": f"Bearer {token}"}


ADMIN_H = bearer(ADMIN_USER)
CLINIC_H = bearer(CLINICIAN_USER)


def _lookup_user(conn, username: str) -> dict | None:  # noqa: ARG001
    return USER_DB.get(username)


# ── Session-scoped fixtures ───────────────────────────────────────────────────

@pytest.fixture(scope="session", autouse=True)
def override_db():
    """Replace get_db with a MagicMock for all tests."""
    from app.main import app
    app.dependency_overrides[get_db] = lambda: MOCK_CONN
    yield
    app.dependency_overrides.pop(get_db, None)


@pytest.fixture(scope="session", autouse=True)
def patch_user_lookup():
    """Patch the username→user lookup used by JWT validation in deps.py."""
    with patch("app.api.deps.get_by_username", side_effect=_lookup_user):
        yield


@pytest.fixture(scope="session", autouse=True)
def stub_clinical_summary():
    """Triage session detail calls generate_summary when summary is empty.

    With ``AI_SUMMARY=true`` in a developer ``.env``, that would load PyTorch /
    HuggingFace and block or slow pytest for minutes. Stub the service so API
    tests stay fast and independent of local ML configuration.
    """
    with patch(
        "app.services.summary.generate_summary",
        return_value=("Stub clinical summary for API tests.", False),
    ):
        yield


@pytest.fixture(scope="session")
def client():
    from app.main import app
    with TestClient(app, raise_server_exceptions=True) as c:
        yield c
