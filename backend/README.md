# TRIBOT Backend

FastAPI backend for the TRIBOT Clinical Translation Platform — Royal Australian Hospital.  
Supports role-based auth, admin portal, patient-first triage sessions, real-time EN↔AR translation (SMaLL-100), vitals tracking, ATS categorisation, session history, and PDF export.

---

## What is implemented

### Authentication & role-based access
- `POST /api/v1/auth/login` — sign in with email + password, returns a JWT bearer token
- `GET /api/v1/auth/me` — returns the currently authenticated user

| Role | Portal access |
|---|---|
| **Admin** | Admin portal (`/admin/*`) + all triage/translate/patient/log routes |
| **Clinician** | Triage portal only (triage, translate, patients, logs) |

Wrong-role requests return **HTTP 403 Forbidden**. Unauthenticated requests return **HTTP 401 Unauthorized**.

### Admin portal
- `GET /admin/users` — list all users with optional search; includes last-login timestamp
- `POST /admin/users` — create admin or clinician; returns a one-time temporary password
- `GET /admin/users/{id}` — get a single user
- `PUT /admin/users/{id}` — update name or role (role changes are auto-logged)
- `POST /admin/users/{id}/deactivate` / `reactivate` — toggle account status
- `DELETE /admin/users/{id}` — permanently delete a user
- `GET /admin/change-log` — paginated audit trail of all admin actions; supports `from_date`, `to_date`, `limit`, `offset`
- `GET /admin/sessions` — all completed triage sessions; supports `search`, `limit`, `offset`
- `DELETE /admin/sessions/{id}` — delete a session transcript (auto-logged)

### Triage portal
- **Patient search** — by name, MRN, or ID; full CRUD
- **Triage sessions** — create, patch vitals + ATS, submit
- **Chat messages** — per-session bilingual message log with translation and confidence scores
- **Session history** — paginated list of completed sessions
- **PDF export** — downloadable report with patient info, vitals, ATS, full transcript, and clinical summary

### Translation
- `POST /api/v1/translate` — EN↔AR translation using **SMaLL-100** (`alirezamsh/small100`)
- Confidence scoring, red-flag escalation detection, full audit logging

### PDF clinical summary
- Rule-based summary generated instantly by default
- Optional AI summary using `google/flan-t5-small` (set `AI_SUMMARY=true` in `.env`)

### Database
PostgreSQL with auto-migration on startup (`schema.sql` → `migrations.sql`).

| Table | Purpose |
|---|---|
| `users` | Clinicians and admins |
| `login_attempts` | Login audit trail |
| `patients` | Patient registry |
| `triage_sessions` | Session records (vitals, ATS, status) |
| `triage_messages` | Per-session bilingual messages |
| `translation_logs` | Raw translation audit log |
| `admin_audit_log` | Admin portal change log |

---

## Project structure

```text
backend/
├── app/
│   ├── api/
│   │   ├── deps.py              # get_current_user / get_current_admin / get_current_clinician
│   │   └── routes/
│   │       ├── auth.py          # POST /auth/login, GET /auth/me
│   │       ├── admin.py         # All /admin/* endpoints
│   │       ├── patients.py      # Patient CRUD + search
│   │       ├── triage.py        # Sessions, messages, submit, history, PDF export
│   │       ├── translate.py     # Standalone translation
│   │       ├── logs.py          # Translation audit log query
│   │       └── health.py        # GET /health
│   ├── core/
│   │   ├── config.py            # Settings loaded from .env
│   │   ├── errors.py            # BadRequestError, UnauthorizedError, ForbiddenError, ConflictError
│   │   ├── security.py          # PBKDF2 password hashing, JWT create/decode
│   │   └── utils.py             # utcnow_iso helper
│   ├── data/
│   │   ├── schema.sql           # Base DDL (CREATE TABLE IF NOT EXISTS)
│   │   ├── migrations.sql       # Idempotent ALTER TABLE / CREATE TABLE (run on every startup)
│   │   └── database.py          # psycopg2 connection helpers, init_db()
│   ├── repositories/            # Raw SQL data access — no ORM
│   │   ├── users.py             # list, get, create, update, delete, last_login
│   │   ├── admin_audit_log.py   # create_log, list_logs, count_logs
│   │   ├── patients.py
│   │   ├── triage_sessions.py
│   │   ├── triage_messages.py
│   │   ├── translation_logs.py
│   │   ├── login_attempts.py
│   │   └── demo_seed.py         # Seeds demo triage session on startup
│   ├── schemas/                 # Pydantic v2 request/response models
│   │   ├── admin.py             # CreateUserRequest, UserListItem, ChangeLogEntry, ...
│   │   ├── auth.py              # LoginRequest (email), TokenResponse
│   │   ├── users.py             # UserResponse (email field)
│   │   ├── triage.py
│   │   ├── translation.py
│   │   └── logs.py
│   ├── services/
│   │   ├── auth.py              # login / signup business logic
│   │   ├── translator.py        # SMaLL-100 translation + logging
│   │   ├── pdf.py               # PDF generation (ReportLab)
│   │   ├── summary.py           # Clinical summary (rule-based + optional Flan-T5)
│   │   └── ai/                  # Model loader, tokenizer, inference
│   ├── main.py                  # App entrypoint, exception handlers, lifespan (DB init + seeding)
│   └── seed.py                  # CLI seeding script
└── tests/
    ├── conftest.py              # Shared fixtures: mock users, DB override, JWT tokens
    └── test_api.py              # 55 endpoint tests — no real DB required
```

---

## Run locally

### 1. PostgreSQL

See [POSTGRESQL_SETUP.md](POSTGRESQL_SETUP.md) for full setup instructions (create database, user, grants).

### 2. Python environment

```bash
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
# Edit .env — at minimum set DB_PASSWORD and SECRET_KEY
```

### 3. Start the server

```bash
make run
# or directly:
uvicorn app.main:app --reload
```

> On macOS, prefix with `GLOG_minloglevel=3` to suppress a harmless PyTorch C++ log line.

Open:
- Swagger UI: `http://127.0.0.1:8000/docs`
- Health check: `http://127.0.0.1:8000/api/v1/health`

---

## API reference

### Auth
| Method | Path | Auth | Description |
|--------|------|------|-------------|
| `POST` | `/api/v1/auth/login` | — | Sign in; returns JWT + user role |
| `GET` | `/api/v1/auth/me` | Any | Return current user |

### Admin portal  _(admin role required)_
| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/api/v1/admin/users` | List all users (`?search=`) |
| `POST` | `/api/v1/admin/users` | Create user; returns temporary password |
| `GET` | `/api/v1/admin/users/{id}` | Get user |
| `PUT` | `/api/v1/admin/users/{id}` | Update name / role |
| `POST` | `/api/v1/admin/users/{id}/deactivate` | Deactivate user |
| `POST` | `/api/v1/admin/users/{id}/reactivate` | Reactivate user |
| `DELETE` | `/api/v1/admin/users/{id}` | Delete user |
| `GET` | `/api/v1/admin/change-log` | Audit trail (`?from_date=&to_date=&limit=&offset=`) |
| `GET` | `/api/v1/admin/sessions` | All completed sessions (`?search=&limit=&offset=`) |
| `DELETE` | `/api/v1/admin/sessions/{id}` | Delete session transcript |

### Triage portal  _(clinician or admin)_
| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/api/v1/patients` | List patients |
| `GET` | `/api/v1/patients/search?q=` | Search by name, MRN, or ID |
| `GET` | `/api/v1/patients/{id}` | Get patient |
| `POST` | `/api/v1/patients` | Create patient |
| `PATCH` | `/api/v1/patients/{id}` | Update patient |
| `DELETE` | `/api/v1/patients/{id}` | Delete patient |
| `POST` | `/api/v1/triage/sessions` | Start triage session |
| `GET` | `/api/v1/triage/sessions/active?patient_id=` | Get active session for patient |
| `GET` | `/api/v1/triage/sessions/{id}` | Session detail + messages |
| `PATCH` | `/api/v1/triage/sessions/{id}` | Auto-save vitals / ATS |
| `POST` | `/api/v1/triage/sessions/{id}/messages` | Send message (auto-translates) |
| `POST` | `/api/v1/triage/sessions/{id}/submit` | Submit session (requires vitals + ATS) |
| `GET` | `/api/v1/triage/sessions/{id}/logs` | Per-session translation audit log |
| `GET` | `/api/v1/triage/sessions/{id}/export.pdf` | Download PDF report |
| `GET` | `/api/v1/triage/history` | Completed session history |
| `POST` | `/api/v1/translate` | Standalone translation |
| `GET` | `/api/v1/logs` | Translation audit log (escalation filter) |

---

## Environment variables

| Variable | Default | Description |
|---|---|---|
| `SECRET_KEY` | `change-me-...` | JWT signing secret — **change in production** |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | `60` | Token lifetime |
| `DB_HOST` | `localhost` | PostgreSQL host |
| `DB_PORT` | `5432` | PostgreSQL port |
| `DB_NAME` | `tribot` | Database name |
| `DB_USER` | `postgres` | Database user |
| `DB_PASSWORD` | _(empty)_ | Database password |
| `LOW_CONFIDENCE_THRESHOLD` | `70` | Translation confidence threshold (0–100) |
| `SEED_DEMO_ADMIN` | `true` | Auto-create demo admin on startup |
| `DEMO_ADMIN_EMAIL` | `admin@hospital.au` | Demo admin email |
| `DEMO_ADMIN_PASSWORD` | `AdminPass123!` | Demo admin password |
| `SEED_DEMO_USER` | `true` | Auto-create demo clinician on startup |
| `DEMO_EMAIL` | `clinician1@hospital.au` | Demo clinician email |
| `DEMO_PASSWORD` | `ChangeMe123!` | Demo clinician password |
| `SEED_DEMO_PATIENTS` | `true` | Seed sample patients + session on startup |
| `AI_MODEL_PATH` | `alirezamsh/small100` | HuggingFace translation model |
| `AI_DEVICE` | `auto` | `cpu`, `cuda`, `mps`, or `auto` |
| `AI_NUM_BEAMS` | `4` | Beam search width (1 = greedy/fast, 4 = better quality) |
| `AI_MAX_NEW_TOKENS` | `256` | Max tokens per translation |
| `AI_USE_FLOAT16` | `false` | Enable FP16 for GPU inference |
| `AI_WARMUP_ON_START` | `false` | Load model at startup in background thread |
| `SUMMARY_MODEL_PATH` | `google/flan-t5-small` | PDF summary model |
| `GLOG_minloglevel` | `3` | Suppress PyTorch C++ log noise on macOS |

---

## Demo accounts

Seeded automatically on first startup:

| Account | Email | Password | Role |
|---|---|---|---|
| Demo Admin | `admin@hospital.au` | `AdminPass123!` | admin |
| Demo Clinician | `clinician1@hospital.au` | `ChangeMe123!` | clinician |

Set `SEED_DEMO_ADMIN=false` / `SEED_DEMO_USER=false` in `.env` to disable.

---

## Quick API examples

### Login
```bash
curl -X POST http://127.0.0.1:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@hospital.au","password":"AdminPass123!"}'
```
Response includes `access_token` and `user.role` — use role to redirect to the correct portal.

### Add a user (admin portal)
```bash
curl -X POST http://127.0.0.1:8000/api/v1/admin/users \
  -H "Authorization: Bearer <ADMIN_TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{"full_name":"Sarah Chen","email":"sarah.chen@hospital.au","role":"clinician"}'
```
Returns the new user + `temporary_password`.

### Translate (triage portal)
```bash
curl -X POST http://127.0.0.1:8000/api/v1/translate \
  -H "Authorization: Bearer <CLINICIAN_TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{"source_text":"chest pain","source_language":"en","target_language":"ar"}'
```

---

## Running tests

No real database required — all repository calls are mocked.

```bash
cd backend
pytest tests/ -v
```

**55 tests** covering:
- Auth — login success/failure, `/me`, bad tokens, inactive accounts
- Role enforcement — 403 for wrong role, 401 for unauthenticated
- Admin users — full CRUD, deactivate/reactivate, self-delete/deactivate protection
- Admin change log — entries, date filters, pagination
- Admin sessions — list, delete
- Patients — list, search, create, duplicate MRN
- Triage — create, patch vitals, post messages, submit, history
- Translate — clinician and admin access, unauthenticated blocked

---

## Translation performance

| Setting | First request | Subsequent |
|---|---|---|
| `AI_NUM_BEAMS=1` (greedy) | 30–60 s (model loads) | ~1–3 s |
| `AI_NUM_BEAMS=4` (beam search) | 30–60 s | ~5–10 s |
| `AI_WARMUP_ON_START=true` | Model loads in background at startup | ~1–3 s |
