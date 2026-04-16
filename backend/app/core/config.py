from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parents[2]
load_dotenv(BASE_DIR / ".env")


class Settings:
    def __init__(self) -> None:
        self.app_name = os.getenv("APP_NAME", "TRIBOT Backend API")
        self.api_prefix = "/api/v1"
        self.app_version = "0.1.0"
        self.secret_key = os.getenv("SECRET_KEY", "change-me-for-production")
        self.jwt_algorithm = "HS256"
        self.access_token_expire_minutes = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "60"))
        self.low_confidence_threshold = float(os.getenv("LOW_CONFIDENCE_THRESHOLD", "70"))
        
        # PostgreSQL configuration
        self.db_host = os.getenv("DB_HOST", "localhost")
        self.db_port = int(os.getenv("DB_PORT", "5432"))
        self.db_name = os.getenv("DB_NAME", "tribot")
        self.db_user = os.getenv("DB_USER") or os.getenv("USER", "postgres")
        self.db_password = os.getenv("DB_PASSWORD", "")
        
        self.seed_demo_user = os.getenv("SEED_DEMO_USER", "true").lower() == "true"
        self.seed_demo_patients = os.getenv("SEED_DEMO_PATIENTS", "true").lower() == "true"
        self.demo_email = os.getenv("DEMO_EMAIL", "clinician1@hospital.au")
        self.demo_password = os.getenv("DEMO_PASSWORD", "ChangeMe123!")

        self.seed_demo_admin = os.getenv("SEED_DEMO_ADMIN", "true").lower() == "true"
        self.demo_admin_email = os.getenv("DEMO_ADMIN_EMAIL", "admin@hospital.au")
        self.demo_admin_password = os.getenv("DEMO_ADMIN_PASSWORD", "AdminPass123!")
        self.supported_languages = {"en", "english", "ar", "arabic"}

        # AI / SMaLL-100 configuration
        self.ai_model_path = os.getenv("AI_MODEL_PATH", "alirezamsh/small100")
        self.ai_device = os.getenv("AI_DEVICE", "auto")
        self.ai_num_beams = int(os.getenv("AI_NUM_BEAMS", "1"))
        self.ai_max_new_tokens = int(os.getenv("AI_MAX_NEW_TOKENS", "128"))
        self.ai_warmup_on_start = os.getenv("AI_WARMUP_ON_START", "false").lower() == "true"

        # Summary model — set AI_SUMMARY=true to use flan-t5-base (may hallucinate on small sessions).
        # Default is rule-based: always accurate, never hallucinates.
        self.ai_summary_enabled = os.getenv("AI_SUMMARY").lower() == "true"
        self.summary_model_path = os.getenv("SUMMARY_MODEL_PATH", "google/flan-t5-base")


@lru_cache
def get_settings() -> Settings:
    return Settings()
