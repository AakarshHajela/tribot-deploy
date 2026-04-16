"""End-to-end API tests for all TRIBOT backend endpoints.

Run with:
    cd backend
    pytest tests/ -v

No real database is needed — repository calls are patched per-test to return
controlled fixture data defined in conftest.py.
"""
from __future__ import annotations

from unittest.mock import MagicMock, patch

from tests.conftest import (
    ADMIN_H,
    ADMIN_USER,
    CLINIC_H,
    CLINICIAN_USER,
    CLINICIAN_PASSWORD,
    ADMIN_PASSWORD,
    INACTIVE_USER,
    INACTIVE_PASSWORD,
    MOCK_AUDIT_LOG,
    MOCK_CONN,
    MOCK_PATIENT,
    MOCK_SESSION_ROW,
    _lookup_user,
)

BASE = "/api/v1"


# ══════════════════════════════════════════════════════════════════════════════
# 1.  Health
# ══════════════════════════════════════════════════════════════════════════════

class TestHealth:
    def test_health_returns_ok(self, client):
        r = client.get(f"{BASE}/health")
        assert r.status_code == 200
        assert r.json()["status"] == "ok"


# ══════════════════════════════════════════════════════════════════════════════
# 2.  Auth  —  POST /auth/login  |  GET /auth/me
# ══════════════════════════════════════════════════════════════════════════════

class TestAuth:
    # helpers so every login test shares the same two patches
    @staticmethod
    def _login(client, email: str, password: str):
        with patch("app.repositories.users.get_by_username", side_effect=_lookup_user), \
             patch("app.repositories.login_attempts.create_attempt", return_value={}):
            return client.post(f"{BASE}/auth/login", json={"email": email, "password": password})

    # ── login success ────────────────────────────────────────────────────────

    def test_admin_login_returns_token_and_role(self, client):
        r = self._login(client, ADMIN_USER["username"], ADMIN_PASSWORD)
        assert r.status_code == 200
        body = r.json()
        assert "access_token" in body
        assert body["token_type"] == "bearer"
        assert body["user"]["role"] == "admin"
        assert body["user"]["email"] == ADMIN_USER["username"]

    def test_clinician_login_returns_token_and_role(self, client):
        r = self._login(client, CLINICIAN_USER["username"], CLINICIAN_PASSWORD)
        assert r.status_code == 200
        assert r.json()["user"]["role"] == "clinician"

    # ── login failures ───────────────────────────────────────────────────────

    def test_wrong_password_returns_401(self, client):
        r = self._login(client, ADMIN_USER["username"], "WrongPassword!")
        assert r.status_code == 401

    def test_unknown_email_returns_401(self, client):
        with patch("app.repositories.users.get_by_username", return_value=None), \
             patch("app.repositories.login_attempts.create_attempt", return_value={}):
            r = client.post(f"{BASE}/auth/login", json={"email": "ghost@x.com", "password": "X"})
        assert r.status_code == 401

    def test_inactive_user_returns_401(self, client):
        r = self._login(client, INACTIVE_USER["username"], INACTIVE_PASSWORD)
        assert r.status_code == 401

    def test_empty_email_returns_400(self, client):
        r = client.post(f"{BASE}/auth/login", json={"email": "", "password": "pass"})
        assert r.status_code == 400

    # ── /me ──────────────────────────────────────────────────────────────────

    def test_me_returns_admin_user(self, client):
        r = client.get(f"{BASE}/auth/me", headers=ADMIN_H)
        assert r.status_code == 200
        assert r.json()["role"] == "admin"
        assert r.json()["email"] == ADMIN_USER["username"]

    def test_me_returns_clinician_user(self, client):
        r = client.get(f"{BASE}/auth/me", headers=CLINIC_H)
        assert r.status_code == 200
        assert r.json()["role"] == "clinician"

    def test_me_without_token_returns_401(self, client):
        r = client.get(f"{BASE}/auth/me")
        assert r.status_code == 401

    def test_me_with_bad_token_returns_401(self, client):
        r = client.get(f"{BASE}/auth/me", headers={"Authorization": "Bearer bad.token.here"})
        assert r.status_code == 401


# ══════════════════════════════════════════════════════════════════════════════
# 3.  Role enforcement
# ══════════════════════════════════════════════════════════════════════════════

class TestRoleEnforcement:
    """Clinicians must be blocked from admin routes; admins can use triage routes."""

    def test_clinician_blocked_from_list_users(self, client):
        r = client.get(f"{BASE}/admin/users", headers=CLINIC_H)
        assert r.status_code == 403

    def test_clinician_blocked_from_change_log(self, client):
        r = client.get(f"{BASE}/admin/change-log", headers=CLINIC_H)
        assert r.status_code == 403

    def test_clinician_blocked_from_admin_sessions(self, client):
        r = client.get(f"{BASE}/admin/sessions", headers=CLINIC_H)
        assert r.status_code == 403

    def test_clinician_blocked_from_create_user(self, client):
        r = client.post(f"{BASE}/admin/users", headers=CLINIC_H,
                        json={"full_name": "X", "email": "x@x.au", "role": "clinician"})
        assert r.status_code == 403

    def test_unauthenticated_blocked_from_admin(self, client):
        r = client.get(f"{BASE}/admin/users")
        assert r.status_code == 401

    def test_unauthenticated_blocked_from_triage(self, client):
        r = client.get(f"{BASE}/triage/history")
        assert r.status_code == 401

    def test_unauthenticated_blocked_from_patients(self, client):
        r = client.get(f"{BASE}/patients")
        assert r.status_code == 401

    def test_admin_can_access_triage_history(self, client):
        with patch("app.repositories.triage_sessions.count_completed_history", return_value=0), \
             patch("app.repositories.triage_sessions.list_completed_history", return_value=[]):
            r = client.get(f"{BASE}/triage/history", headers=ADMIN_H)
        assert r.status_code == 200

    def test_admin_can_list_patients(self, client):
        with patch("app.repositories.patients.count_all", return_value=0), \
             patch("app.repositories.patients.list_all", return_value=[]):
            r = client.get(f"{BASE}/patients", headers=ADMIN_H)
        assert r.status_code == 200


# ══════════════════════════════════════════════════════════════════════════════
# 4.  Admin — User Management
# ══════════════════════════════════════════════════════════════════════════════

class TestAdminUsers:

    def test_list_users(self, client):
        with patch("app.repositories.users.list_all_users", return_value=[CLINICIAN_USER, ADMIN_USER]), \
             patch("app.repositories.users.get_last_login", return_value=None):
            r = client.get(f"{BASE}/admin/users", headers=ADMIN_H)
        assert r.status_code == 200
        body = r.json()
        assert body["total"] == 2
        emails = [u["email"] for u in body["items"]]
        assert CLINICIAN_USER["username"] in emails

    def test_list_users_search(self, client):
        with patch("app.repositories.users.list_all_users", return_value=[CLINICIAN_USER]), \
             patch("app.repositories.users.get_last_login", return_value=None):
            r = client.get(f"{BASE}/admin/users?search=doc", headers=ADMIN_H)
        assert r.status_code == 200
        assert r.json()["total"] == 1

    def test_get_user_by_id(self, client):
        with patch("app.repositories.users.get_by_id", return_value=CLINICIAN_USER), \
             patch("app.repositories.users.get_last_login", return_value="2024-03-23T14:30:00Z"):
            r = client.get(f"{BASE}/admin/users/{CLINICIAN_USER['id']}", headers=ADMIN_H)
        assert r.status_code == 200
        assert r.json()["email"] == CLINICIAN_USER["username"]
        assert r.json()["last_login"] == "2024-03-23T14:30:00Z"

    def test_get_user_not_found(self, client):
        with patch("app.repositories.users.get_by_id", return_value=None):
            r = client.get(f"{BASE}/admin/users/nonexistent", headers=ADMIN_H)
        assert r.status_code == 400

    def test_create_clinician_returns_temp_password(self, client):
        new_user = {**CLINICIAN_USER, "id": "new-001", "username": "newdoc@hospital.au"}
        with patch("app.repositories.users.get_by_username", return_value=None), \
             patch("app.repositories.users.create_user", return_value=new_user), \
             patch("app.repositories.admin_audit_log.create_log", return_value={}), \
             patch("app.repositories.users.get_last_login", return_value=None):
            r = client.post(f"{BASE}/admin/users", headers=ADMIN_H, json={
                "full_name": "New Doctor",
                "email": "newdoc@hospital.au",
                "role": "clinician",
            })
        assert r.status_code == 201
        body = r.json()
        assert "temporary_password" in body
        assert len(body["temporary_password"]) >= 12
        assert body["user"]["role"] == "clinician"
        assert body["user"]["email"] == "newdoc@hospital.au"

    def test_create_admin_role(self, client):
        new_admin = {**ADMIN_USER, "id": "new-admin-001", "username": "newadmin@hospital.au"}
        with patch("app.repositories.users.get_by_username", return_value=None), \
             patch("app.repositories.users.create_user", return_value=new_admin), \
             patch("app.repositories.admin_audit_log.create_log", return_value={}), \
             patch("app.repositories.users.get_last_login", return_value=None):
            r = client.post(f"{BASE}/admin/users", headers=ADMIN_H, json={
                "full_name": "New Admin",
                "email": "newadmin@hospital.au",
                "role": "admin",
            })
        assert r.status_code == 201
        assert r.json()["user"]["role"] == "admin"

    def test_create_user_duplicate_email_returns_409(self, client):
        with patch("app.repositories.users.get_by_username", return_value=CLINICIAN_USER):
            r = client.post(f"{BASE}/admin/users", headers=ADMIN_H, json={
                "full_name": "Dup",
                "email": CLINICIAN_USER["username"],
                "role": "clinician",
            })
        assert r.status_code == 409

    def test_create_user_invalid_role_returns_400(self, client):
        r = client.post(f"{BASE}/admin/users", headers=ADMIN_H, json={
            "full_name": "Bad",
            "email": "bad@hospital.au",
            "role": "superuser",
        })
        assert r.status_code == 400

    def test_update_user_role_logs_change(self, client):
        updated = {**CLINICIAN_USER, "role": "admin"}
        with patch("app.repositories.users.get_by_id", return_value=CLINICIAN_USER), \
             patch("app.repositories.users.update_user", return_value=updated), \
             patch("app.repositories.admin_audit_log.create_log", return_value={}) as mock_log, \
             patch("app.repositories.users.get_last_login", return_value=None):
            r = client.put(f"{BASE}/admin/users/{CLINICIAN_USER['id']}", headers=ADMIN_H,
                           json={"role": "admin"})
        assert r.status_code == 200
        assert r.json()["role"] == "admin"
        mock_log.assert_called_once()
        call_kwargs = mock_log.call_args.kwargs
        assert call_kwargs["action_type"] == "role_modified"

    def test_update_user_name_no_audit_log(self, client):
        updated = {**CLINICIAN_USER, "full_name": "New Name"}
        with patch("app.repositories.users.get_by_id", return_value=CLINICIAN_USER), \
             patch("app.repositories.users.update_user", return_value=updated), \
             patch("app.repositories.admin_audit_log.create_log", return_value={}) as mock_log, \
             patch("app.repositories.users.get_last_login", return_value=None):
            r = client.put(f"{BASE}/admin/users/{CLINICIAN_USER['id']}", headers=ADMIN_H,
                           json={"full_name": "New Name"})
        assert r.status_code == 200
        mock_log.assert_not_called()

    def test_deactivate_user(self, client):
        deactivated = {**CLINICIAN_USER, "is_active": False}
        with patch("app.repositories.users.get_by_id", return_value=CLINICIAN_USER), \
             patch("app.repositories.users.update_user", return_value=deactivated), \
             patch("app.repositories.admin_audit_log.create_log", return_value={}), \
             patch("app.repositories.users.get_last_login", return_value=None):
            r = client.post(f"{BASE}/admin/users/{CLINICIAN_USER['id']}/deactivate", headers=ADMIN_H)
        assert r.status_code == 200
        assert r.json()["is_active"] is False

    def test_deactivate_already_inactive_returns_400(self, client):
        with patch("app.repositories.users.get_by_id", return_value={**CLINICIAN_USER, "is_active": False}):
            r = client.post(f"{BASE}/admin/users/{CLINICIAN_USER['id']}/deactivate", headers=ADMIN_H)
        assert r.status_code == 400

    def test_deactivate_self_returns_400(self, client):
        with patch("app.repositories.users.get_by_id", return_value=ADMIN_USER):
            r = client.post(f"{BASE}/admin/users/{ADMIN_USER['id']}/deactivate", headers=ADMIN_H)
        assert r.status_code == 400

    def test_reactivate_user(self, client):
        inactive = {**CLINICIAN_USER, "is_active": False}
        reactivated = {**CLINICIAN_USER, "is_active": True}
        with patch("app.repositories.users.get_by_id", return_value=inactive), \
             patch("app.repositories.users.update_user", return_value=reactivated), \
             patch("app.repositories.admin_audit_log.create_log", return_value={}), \
             patch("app.repositories.users.get_last_login", return_value=None):
            r = client.post(f"{BASE}/admin/users/{CLINICIAN_USER['id']}/reactivate", headers=ADMIN_H)
        assert r.status_code == 200
        assert r.json()["is_active"] is True

    def test_reactivate_already_active_returns_400(self, client):
        with patch("app.repositories.users.get_by_id", return_value=CLINICIAN_USER):
            r = client.post(f"{BASE}/admin/users/{CLINICIAN_USER['id']}/reactivate", headers=ADMIN_H)
        assert r.status_code == 400

    def test_delete_user(self, client):
        with patch("app.repositories.users.get_by_id", return_value=CLINICIAN_USER), \
             patch("app.repositories.users.delete_user", return_value=True), \
             patch("app.repositories.admin_audit_log.create_log", return_value={}):
            r = client.delete(f"{BASE}/admin/users/{CLINICIAN_USER['id']}", headers=ADMIN_H)
        assert r.status_code == 204

    def test_delete_self_returns_400(self, client):
        with patch("app.repositories.users.get_by_id", return_value=ADMIN_USER):
            r = client.delete(f"{BASE}/admin/users/{ADMIN_USER['id']}", headers=ADMIN_H)
        assert r.status_code == 400

    def test_delete_nonexistent_user_returns_400(self, client):
        with patch("app.repositories.users.get_by_id", return_value=None):
            r = client.delete(f"{BASE}/admin/users/ghost", headers=ADMIN_H)
        assert r.status_code == 400


# ══════════════════════════════════════════════════════════════════════════════
# 5.  Admin — Change Log
# ══════════════════════════════════════════════════════════════════════════════

class TestAdminChangeLog:

    def test_returns_log_entries(self, client):
        with patch("app.repositories.admin_audit_log.list_logs", return_value=[MOCK_AUDIT_LOG]), \
             patch("app.repositories.admin_audit_log.count_logs", return_value=1):
            r = client.get(f"{BASE}/admin/change-log", headers=ADMIN_H)
        assert r.status_code == 200
        body = r.json()
        assert body["total"] == 1
        entry = body["items"][0]
        assert entry["action_type"] == "user_created"
        assert entry["admin_user"] == ADMIN_USER["username"]
        assert entry["target"] == CLINICIAN_USER["full_name"]

    def test_date_filter_forwarded_to_repo(self, client):
        with patch("app.repositories.admin_audit_log.list_logs", return_value=[]) as mock_list, \
             patch("app.repositories.admin_audit_log.count_logs", return_value=0):
            r = client.get(
                f"{BASE}/admin/change-log?from_date=2024-03-01&to_date=2024-03-31",
                headers=ADMIN_H,
            )
        assert r.status_code == 200
        call_kwargs = mock_list.call_args.kwargs
        assert call_kwargs["from_date"] == "2024-03-01"
        assert call_kwargs["to_date"] == "2024-03-31"

    def test_pagination_params(self, client):
        with patch("app.repositories.admin_audit_log.list_logs", return_value=[]) as mock_list, \
             patch("app.repositories.admin_audit_log.count_logs", return_value=0):
            r = client.get(f"{BASE}/admin/change-log?limit=10&offset=20", headers=ADMIN_H)
        assert r.status_code == 200
        call_kwargs = mock_list.call_args.kwargs
        assert call_kwargs["limit"] == 10
        assert call_kwargs["offset"] == 20

    def test_empty_log(self, client):
        with patch("app.repositories.admin_audit_log.list_logs", return_value=[]), \
             patch("app.repositories.admin_audit_log.count_logs", return_value=0):
            r = client.get(f"{BASE}/admin/change-log", headers=ADMIN_H)
        assert r.status_code == 200
        assert r.json() == {"items": [], "total": 0}


# ══════════════════════════════════════════════════════════════════════════════
# 6.  Admin — Session History
# ══════════════════════════════════════════════════════════════════════════════

class TestAdminSessions:

    def test_list_sessions(self, client):
        with patch("app.repositories.triage_sessions.list_completed_history",
                   return_value=[MOCK_SESSION_ROW]), \
             patch("app.repositories.triage_sessions.count_completed_history", return_value=1):
            r = client.get(f"{BASE}/admin/sessions", headers=ADMIN_H)
        assert r.status_code == 200
        body = r.json()
        assert body["total"] == 1
        assert body["items"][0]["mrn"] == MOCK_PATIENT["mrn"]
        assert body["items"][0]["patient_name"] == MOCK_PATIENT["full_name"]
        assert body["items"][0]["ats_category"] == 2

    def test_list_sessions_search(self, client):
        with patch("app.repositories.triage_sessions.list_completed_history",
                   return_value=[]) as mock_list, \
             patch("app.repositories.triage_sessions.count_completed_history", return_value=0):
            r = client.get(f"{BASE}/admin/sessions?search=Ahmed", headers=ADMIN_H)
        assert r.status_code == 200
        assert mock_list.call_args.kwargs["search"] == "Ahmed"

    def test_delete_session(self, client):
        full_session = {
            "id": "session-uuid-001",
            "patient_id": MOCK_PATIENT["id"],
            "provider_id": CLINICIAN_USER["id"],
            "status": "completed",
            "started_at": "2024-03-24T09:15:00Z",
            "ended_at": "2024-03-24T09:27:34Z",
            "duration_seconds": 754,
            "patient_language": "ar",
            "bp_systolic": 120, "bp_diastolic": 80, "heart_rate": 72,
            "temperature": 36.5, "respiratory_rate": 16, "spo2": 98,
            "ats_category": 2, "nurse_confirmed_ats": True,
            "avg_translation_confidence": 0.91,
        }
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = (MOCK_PATIENT["full_name"], MOCK_PATIENT["mrn"])
        MOCK_CONN.cursor.return_value.__enter__.return_value = mock_cursor

        with patch("app.repositories.triage_sessions.get_by_id", return_value=full_session), \
             patch("app.repositories.admin_audit_log.create_log", return_value={}):
            r = client.delete(f"{BASE}/admin/sessions/session-uuid-001", headers=ADMIN_H)
        assert r.status_code == 204

    def test_delete_session_not_found(self, client):
        with patch("app.repositories.triage_sessions.get_by_id", return_value=None):
            r = client.delete(f"{BASE}/admin/sessions/nonexistent", headers=ADMIN_H)
        assert r.status_code == 400


# ══════════════════════════════════════════════════════════════════════════════
# 7.  Patients  (clinician + admin access)
# ══════════════════════════════════════════════════════════════════════════════

class TestPatients:

    def test_list_patients(self, client):
        with patch("app.repositories.patients.count_all", return_value=1), \
             patch("app.repositories.patients.list_all", return_value=[MOCK_PATIENT]):
            r = client.get(f"{BASE}/patients", headers=CLINIC_H)
        assert r.status_code == 200
        assert r.json()["total"] == 1

    def test_search_patients(self, client):
        with patch("app.repositories.patients.search", return_value=[MOCK_PATIENT]):
            r = client.get(f"{BASE}/patients/search?q=Ahmed", headers=CLINIC_H)
        assert r.status_code == 200
        assert len(r.json()["items"]) == 1
        assert r.json()["items"][0]["mrn"] == MOCK_PATIENT["mrn"]

    def test_get_patient(self, client):
        with patch("app.repositories.patients.get_by_id", return_value=MOCK_PATIENT):
            r = client.get(f"{BASE}/patients/{MOCK_PATIENT['id']}", headers=CLINIC_H)
        assert r.status_code == 200
        assert r.json()["full_name"] == MOCK_PATIENT["full_name"]

    def test_get_patient_not_found(self, client):
        with patch("app.repositories.patients.get_by_id", return_value=None):
            r = client.get(f"{BASE}/patients/ghost", headers=CLINIC_H)
        assert r.status_code == 404

    def test_create_patient(self, client):
        with patch("app.repositories.patients.search", return_value=[]), \
             patch("app.repositories.patients.create_patient", return_value=MOCK_PATIENT):
            r = client.post(f"{BASE}/patients", headers=CLINIC_H, json={
                "mrn": "MRN-2024-0001",
                "full_name": "Ahmed Al-Mansoori",
                "patient_language": "ar",
            })
        assert r.status_code == 201
        assert r.json()["mrn"] == MOCK_PATIENT["mrn"]

    def test_create_patient_duplicate_mrn_returns_409(self, client):
        with patch("app.repositories.patients.search", return_value=[MOCK_PATIENT]):
            r = client.post(f"{BASE}/patients", headers=CLINIC_H, json={
                "mrn": MOCK_PATIENT["mrn"],
                "full_name": "Someone Else",
            })
        assert r.status_code == 409


# ══════════════════════════════════════════════════════════════════════════════
# 8.  Triage  (clinician + admin access)
# ══════════════════════════════════════════════════════════════════════════════

class TestTriage:

    ACTIVE_SESSION: dict = {
        "id": "session-active-001",
        "patient_id": MOCK_PATIENT["id"],
        "provider_id": CLINICIAN_USER["id"],
        "status": "active",
        "started_at": "2024-03-24T09:15:00Z",
        "ended_at": None,
        "duration_seconds": None,
        "patient_language": "ar",
        "bp_systolic": None, "bp_diastolic": None, "heart_rate": None,
        "temperature": None, "respiratory_rate": None, "spo2": None,
        "ats_category": None, "nurse_confirmed_ats": False,
        "avg_translation_confidence": None,
    }

    COMPLETE_SESSION: dict = {
        **ACTIVE_SESSION,
        "status": "completed",
        "ended_at": "2024-03-24T09:27:34Z",
        "duration_seconds": 754,
        "bp_systolic": 120, "bp_diastolic": 80, "heart_rate": 72,
        "temperature": 36.5, "respiratory_rate": 16, "spo2": 98,
        "ats_category": 2, "nurse_confirmed_ats": True,
    }

    def test_create_session(self, client):
        with patch("app.repositories.patients.get_by_id", return_value=MOCK_PATIENT), \
             patch("app.repositories.triage_sessions.get_active_for_patient", return_value=None), \
             patch("app.repositories.triage_sessions.create_session",
                   return_value=self.ACTIVE_SESSION):
            r = client.post(f"{BASE}/triage/sessions", headers=CLINIC_H, json={
                "patient_id": MOCK_PATIENT["id"],
                "patient_language": "ar",
            })
        assert r.status_code == 201
        assert r.json()["status"] == "active"

    def test_create_session_patient_not_found(self, client):
        with patch("app.repositories.patients.get_by_id", return_value=None):
            r = client.post(f"{BASE}/triage/sessions", headers=CLINIC_H,
                            json={"patient_id": "ghost"})
        assert r.status_code == 404

    def test_create_session_already_active_returns_409(self, client):
        with patch("app.repositories.patients.get_by_id", return_value=MOCK_PATIENT), \
             patch("app.repositories.triage_sessions.get_active_for_patient",
                   return_value=self.ACTIVE_SESSION):
            r = client.post(f"{BASE}/triage/sessions", headers=CLINIC_H,
                            json={"patient_id": MOCK_PATIENT["id"]})
        assert r.status_code == 409

    def test_get_active_session(self, client):
        with patch("app.repositories.triage_sessions.get_active_for_patient",
                   return_value=self.ACTIVE_SESSION):
            r = client.get(
                f"{BASE}/triage/sessions/active?patient_id={MOCK_PATIENT['id']}",
                headers=CLINIC_H,
            )
        assert r.status_code == 200
        assert r.json()["status"] == "active"

    def test_get_active_session_none_returns_404(self, client):
        with patch("app.repositories.triage_sessions.get_active_for_patient", return_value=None):
            r = client.get(
                f"{BASE}/triage/sessions/active?patient_id=ghost",
                headers=CLINIC_H,
            )
        assert r.status_code == 404

    def test_get_session_by_id(self, client):
        mock_msg = {
            "id": 1, "session_id": self.ACTIVE_SESSION["id"], "sender": "clinician",
            "original_text": "Are you in pain?", "translated_text": "هل تشعر بألم؟",
            "source_language": "en", "target_language": "ar",
            "confidence": 0.95, "created_at": "2024-03-24T09:16:00Z",
        }
        with patch("app.repositories.triage_sessions.get_by_id",
                   return_value=self.ACTIVE_SESSION), \
             patch("app.repositories.patients.get_by_id", return_value=MOCK_PATIENT), \
             patch("app.repositories.triage_messages.list_by_session", return_value=[mock_msg]):
            r = client.get(
                f"{BASE}/triage/sessions/{self.ACTIVE_SESSION['id']}", headers=CLINIC_H
            )
        assert r.status_code == 200
        assert len(r.json()["messages"]) == 1

    def test_patch_session_vitals(self, client):
        updated = {**self.ACTIVE_SESSION, "bp_systolic": 120, "bp_diastolic": 80}
        with patch("app.repositories.triage_sessions.get_by_id",
                   return_value=self.ACTIVE_SESSION), \
             patch("app.repositories.triage_sessions.update_session_fields",
                   return_value=updated):
            r = client.patch(
                f"{BASE}/triage/sessions/{self.ACTIVE_SESSION['id']}",
                headers=CLINIC_H,
                json={"bp_systolic": 120, "bp_diastolic": 80},
            )
        assert r.status_code == 200

    def test_post_message_with_pre_translated(self, client):
        msg = {
            "id": 1, "session_id": self.ACTIVE_SESSION["id"], "sender": "clinician",
            "original_text": "Hello", "translated_text": "مرحبا",
            "source_language": "en", "target_language": "ar",
            "confidence": 0.95, "created_at": "2024-03-24T09:16:00Z",
        }
        with patch("app.repositories.triage_sessions.get_by_id",
                   return_value=self.ACTIVE_SESSION), \
             patch("app.repositories.triage_messages.create_message", return_value=msg), \
             patch("app.repositories.triage_messages.average_confidence_for_session",
                   return_value=0.95), \
             patch("app.repositories.triage_sessions.update_session_fields",
                   return_value=self.ACTIVE_SESSION):
            r = client.post(
                f"{BASE}/triage/sessions/{self.ACTIVE_SESSION['id']}/messages",
                headers=CLINIC_H,
                json={
                    "sender": "clinician",
                    "original_text": "Hello",
                    "translated_text": "مرحبا",
                    "confidence": 0.95,
                    "source_language": "en",
                    "target_language": "ar",
                },
            )
        assert r.status_code == 201
        assert r.json()["translated_text"] == "مرحبا"

    def test_submit_session(self, client):
        ready = {
            **self.ACTIVE_SESSION,
            "bp_systolic": 120, "bp_diastolic": 80, "heart_rate": 72,
            "temperature": 36.5, "respiratory_rate": 16, "spo2": 98,
            "ats_category": 2,
        }
        with patch("app.repositories.triage_sessions.get_by_id", return_value=ready), \
             patch("app.repositories.triage_sessions.complete_session",
                   return_value=self.COMPLETE_SESSION), \
             patch("app.repositories.patients.get_by_id", return_value=MOCK_PATIENT):
            r = client.post(
                f"{BASE}/triage/sessions/{self.ACTIVE_SESSION['id']}/submit",
                headers=CLINIC_H,
            )
        assert r.status_code == 200
        assert r.json()["session"]["status"] == "completed"

    def test_submit_without_ats_returns_400(self, client):
        with patch("app.repositories.triage_sessions.get_by_id",
                   return_value=self.ACTIVE_SESSION):
            r = client.post(
                f"{BASE}/triage/sessions/{self.ACTIVE_SESSION['id']}/submit",
                headers=CLINIC_H,
            )
        assert r.status_code == 400

    def test_session_history(self, client):
        with patch("app.repositories.triage_sessions.count_completed_history", return_value=1), \
             patch("app.repositories.triage_sessions.list_completed_history",
                   return_value=[MOCK_SESSION_ROW]):
            r = client.get(f"{BASE}/triage/history", headers=CLINIC_H)
        assert r.status_code == 200
        assert r.json()["total"] == 1


# ══════════════════════════════════════════════════════════════════════════════
# 9.  Translate  (clinician + admin access)
# ══════════════════════════════════════════════════════════════════════════════

class TestTranslate:

    # Shape must match ``TranslateResponse`` / ``translate_and_log`` return dict.
    TRANSLATE_RESULT = {
        "session_id": "translate-test-session",
        "timestamp": "2024-03-24T10:00:00Z",
        "translated_text": "مرحبا كيف حالك؟",
        "confidence_score": 0.93,
        "escalation_flag": False,
        "escalation_reason": None,
        "model_name": "small100",
    }

    def test_translate_clinician(self, client):
        # Patch where the route holds its reference (import-time binding), not
        # ``app.services.translator`` — otherwise the real SMaLL-100 path runs.
        with patch("app.api.routes.translate.translate_and_log",
                   return_value=self.TRANSLATE_RESULT):
            r = client.post(f"{BASE}/translate", headers=CLINIC_H, json={
                "source_text": "Hello, how are you?",
                "source_language": "en",
                "target_language": "ar",
            })
        assert r.status_code == 200
        assert r.json()["translated_text"] == self.TRANSLATE_RESULT["translated_text"]

    def test_translate_admin_allowed(self, client):
        with patch("app.api.routes.translate.translate_and_log",
                   return_value=self.TRANSLATE_RESULT):
            r = client.post(f"{BASE}/translate", headers=ADMIN_H, json={
                "source_text": "Hello",
                "source_language": "en",
                "target_language": "ar",
            })
        assert r.status_code == 200

    def test_translate_unauthenticated_blocked(self, client):
        r = client.post(f"{BASE}/translate", json={
            "source_text": "Hello",
            "source_language": "en",
            "target_language": "ar",
        })
        assert r.status_code == 401
