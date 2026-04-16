from __future__ import annotations

from fastapi.middleware.cors import CORSMiddleware

import psycopg2
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.api.routes.admin import router as admin_router
from app.api.routes.auth import router as auth_router
from app.api.routes.health import router as health_router
from app.api.routes.patients import router as patients_router
from app.api.routes.translate import router as translate_router
from app.api.routes.triage import router as triage_router
from app.core.config import get_settings
from app.core.errors import BadRequestError, ConflictError, ForbiddenError, UnauthorizedError
from app.data.database import get_connection, init_db
from app.repositories.demo_seed import seed_demo_triage_session
from app.repositories.patients import ensure_demo_patients
from app.repositories.users import ensure_demo_admin, ensure_demo_user


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    settings = get_settings()
    if settings.seed_demo_user or settings.seed_demo_patients or settings.seed_demo_admin:
        with get_connection() as conn:
            if settings.seed_demo_admin:
                ensure_demo_admin(
                    conn,
                    username=settings.demo_admin_email,
                    password=settings.demo_admin_password,
                )
            if settings.seed_demo_user:
                ensure_demo_user(
                    conn,
                    username=settings.demo_email,
                    password=settings.demo_password,
                )
            if settings.seed_demo_patients:
                ensure_demo_patients(conn)
                seed_demo_triage_session(conn)
    yield


settings = get_settings()

app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    _ = request
    return JSONResponse(
        status_code=400,
        content={
            "detail": "Invalid request.",
            "errors": jsonable_encoder(exc.errors()),
        },
    )


@app.exception_handler(BadRequestError)
async def bad_request_exception_handler(request: Request, exc: BadRequestError):
    _ = request
    return JSONResponse(
        status_code=400,
        content={"detail": exc.message},
    )


@app.exception_handler(UnauthorizedError)
async def unauthorized_exception_handler(request: Request, exc: UnauthorizedError):
    _ = request
    return JSONResponse(
        status_code=401,
        content={"detail": exc.message},
    )


@app.exception_handler(ForbiddenError)
async def forbidden_exception_handler(request: Request, exc: ForbiddenError):
    _ = request
    return JSONResponse(
        status_code=403,
        content={"detail": exc.message},
    )


@app.exception_handler(ConflictError)
async def conflict_exception_handler(request: Request, exc: ConflictError):
    _ = request
    return JSONResponse(
        status_code=409,
        content={"detail": exc.message},
    )


@app.exception_handler(psycopg2.Error)
async def postgres_exception_handler(request: Request, exc: psycopg2.Error):
    _ = request
    return JSONResponse(
        status_code=500,
        content={"detail": f"Database error: {str(exc)}"},
    )


app.include_router(health_router, prefix=settings.api_prefix)
app.include_router(auth_router, prefix=settings.api_prefix)
app.include_router(admin_router, prefix=settings.api_prefix)
app.include_router(patients_router, prefix=settings.api_prefix)
app.include_router(triage_router, prefix=settings.api_prefix)
app.include_router(translate_router, prefix=settings.api_prefix)


@app.get("/")
def root() -> dict[str, str]:
    return {
        "message": "TRIBOT backend is running.",
        "docs": "/docs",
    }
