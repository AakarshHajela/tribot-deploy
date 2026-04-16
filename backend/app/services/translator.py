from __future__ import annotations

import logging
import re
import psycopg2.extensions
import time
from typing import TYPE_CHECKING, Protocol
from uuid import uuid4

if TYPE_CHECKING:
    from app.services.ai.inference import SMaLL100Translator

from app.core.config import get_settings
from app.core.errors import BadRequestError
from app.repositories.translation_logs import create_log

logger = logging.getLogger(__name__)


def normalize_language(value: str) -> str:
    normalized = value.strip().lower()
    mapping = {
        "en": "en",
        "english": "en",
        "ar": "ar",
        "arabic": "ar",
    }
    if normalized not in mapping:
        raise BadRequestError("Unsupported language. Use en/english or ar/arabic.")
    return mapping[normalized]


class Translator(Protocol):
    model_name: str

    def translate(self, text: str, source_language: str, target_language: str) -> tuple[str, float, list[str]]:
        ...


class RuleBasedTranslator:
    model_name = "rule-based-clinical-demo"

    EN_TO_AR_PHRASES = {
        "shortness of breath": "ضيق في التنفس",
        "difficulty breathing": "صعوبة في التنفس",
        "loss of consciousness": "فقدان الوعي",
        "severe bleeding": "نزيف شديد",
        "abdominal pain": "ألم في البطن",
        "chest pain": "ألم في الصدر",
        "high fever": "حمى شديدة",
        "head injury": "إصابة في الرأس",
        "back pain": "ألم الظهر",
        "blood pressure": "ضغط الدم",
        "heart rate": "معدل ضربات القلب",
    }

    EN_TO_AR_WORDS = {
        "patient": "المريض",
        "reports": "يذكر",
        "has": "لديه",
        "and": "و",
        "with": "مع",
        "pain": "ألم",
        "chest": "الصدر",
        "breathing": "التنفس",
        "shortness": "ضيق",
        "breath": "النفس",
        "fever": "حمى",
        "cough": "سعال",
        "vomiting": "قيء",
        "nausea": "غثيان",
        "headache": "صداع",
        "dizziness": "دوخة",
        "diabetes": "سكري",
        "asthma": "ربو",
        "fracture": "كسر",
        "bleeding": "نزيف",
        "unconscious": "فاقد الوعي",
        "severe": "شديد",
        "mild": "خفيف",
        "left": "الأيسر",
        "right": "الأيمن",
        "arm": "الذراع",
        "leg": "الساق",
    }

    RED_FLAGS = {
        "en": {
            "chest pain",
            "difficulty breathing",
            "shortness of breath",
            "loss of consciousness",
            "severe bleeding",
        },
        "ar": {
            "ألم في الصدر",
            "صعوبة في التنفس",
            "ضيق في التنفس",
            "فقدان الوعي",
            "نزيف شديد",
        },
    }

    TOKEN_PATTERN = re.compile(r"__PHRASE_\d+__|[A-Za-z']+|[\u0600-\u06FF]+|\d+|[^\w\s]", flags=re.UNICODE)

    def __init__(self) -> None:
        self.AR_TO_EN_PHRASES = {value: key for key, value in self.EN_TO_AR_PHRASES.items()}
        self.AR_TO_EN_WORDS = {value: key for key, value in self.EN_TO_AR_WORDS.items()}

    def _replace_phrases(
        self,
        text: str,
        phrase_map: dict[str, str],
        *,
        ignore_case: bool,
    ) -> tuple[str, dict[str, str], int]:
        replaced = text
        placeholder_map: dict[str, str] = {}
        match_count = 0

        items = sorted(phrase_map.items(), key=lambda item: len(item[0]), reverse=True)
        for index, (source, target) in enumerate(items):
            placeholder = f"__PHRASE_{index}__"
            flags = re.IGNORECASE if ignore_case else 0
            pattern = re.compile(re.escape(source), flags=flags)
            replaced, count = pattern.subn(placeholder, replaced)
            if count:
                placeholder_map[placeholder] = target
                match_count += count

        return replaced, placeholder_map, match_count

    def _translate_words(
        self,
        text: str,
        word_map: dict[str, str],
        *,
        placeholders: dict[str, str],
    ) -> tuple[str, int, int]:
        raw_tokens = self.TOKEN_PATTERN.findall(text)
        translated_tokens: list[str] = []
        word_count = 0
        match_count = 0

        for token in raw_tokens:
            if token in placeholders:
                translated_tokens.append(placeholders[token])
                continue

            if re.fullmatch(r"[A-Za-z']+|[\u0600-\u06FF]+", token):
                word_count += 1
                mapped = word_map.get(token.lower()) or word_map.get(token)
                if mapped:
                    translated_tokens.append(mapped)
                    match_count += 1
                else:
                    translated_tokens.append(token)
            else:
                translated_tokens.append(token)

        joined = " ".join(translated_tokens)
        joined = re.sub(r"\s+([,.;!?])", r"\1", joined)
        joined = re.sub(r"\s+", " ", joined).strip()
        return joined, word_count, match_count

    def _extract_red_flags(self, text: str, language: str) -> list[str]:
        haystack = text.lower() if language == "en" else text
        matches: list[str] = []
        for term in self.RED_FLAGS[language]:
            candidate = term.lower() if language == "en" else term
            if candidate in haystack:
                matches.append(term)
        return sorted(set(matches))

    def translate(self, text: str, source_language: str, target_language: str) -> tuple[str, float, list[str]]:
        source = normalize_language(source_language)
        target = normalize_language(target_language)

        if source == target:
            red_flags = self._extract_red_flags(text, source)
            return text, 100.0, red_flags

        if {source, target} != {"en", "ar"}:
            raise BadRequestError("Only English <-> Arabic is supported in this starter implementation.")

        if source == "en":
            after_phrases, placeholders, phrase_matches = self._replace_phrases(
                text,
                self.EN_TO_AR_PHRASES,
                ignore_case=True,
            )
            translated, word_count, word_matches = self._translate_words(
                after_phrases,
                self.EN_TO_AR_WORDS,
                placeholders=placeholders,
            )
        else:
            after_phrases, placeholders, phrase_matches = self._replace_phrases(
                text,
                self.AR_TO_EN_PHRASES,
                ignore_case=False,
            )
            translated, word_count, word_matches = self._translate_words(
                after_phrases,
                self.AR_TO_EN_WORDS,
                placeholders=placeholders,
            )

        total_matches = phrase_matches + word_matches
        total_signals = max(word_count + phrase_matches, 1)

        if total_matches == 0:
            confidence = 42.0
        else:
            coverage = min(total_matches / total_signals, 1.0)
            confidence = round(55 + coverage * 40, 2)

        red_flags = self._extract_red_flags(text, source) + self._extract_red_flags(translated, target)
        unique_red_flags = sorted(set(red_flags))

        if unique_red_flags:
            confidence = min(confidence, 68.0)

        return translated, confidence, unique_red_flags


_ai_translator: "SMaLL100Translator | None" = None


def _get_ai_translator() -> "SMaLL100Translator":
    """Return the module-level SMaLL100Translator singleton (lazy init)."""
    global _ai_translator
    if _ai_translator is None:
        from app.services.ai.inference import SMaLL100Translator

        settings = get_settings()
        _ai_translator = SMaLL100Translator(
            model_path=settings.ai_model_path,
            device=settings.ai_device,
            num_beams=settings.ai_num_beams,
            max_new_tokens=settings.ai_max_new_tokens,
        )
    return _ai_translator


def translate_and_log(
    conn: psycopg2.extensions.connection,
    *,
    source_text: str,
    source_language: str,
    target_language: str,
    clinician_id: str,
    session_id: str | None = None,
    translator: Translator | None = None,
) -> dict:
    if translator is None:
        translator = _get_ai_translator()

    settings = get_settings()
    source = normalize_language(source_language)
    target = normalize_language(target_language)

    started = time.perf_counter()
    translated_text, confidence_score, red_flags = translator.translate(source_text, source, target)
    latency_ms = int((time.perf_counter() - started) * 1000)

    escalation_flag = bool(red_flags) or confidence_score < settings.low_confidence_threshold
    escalation_reason = None
    if red_flags:
        escalation_reason = "Red flag terms detected: " + ", ".join(red_flags)
    elif confidence_score < settings.low_confidence_threshold:
        escalation_reason = f"Confidence below threshold ({settings.low_confidence_threshold})."

    log_record = create_log(
        conn,
        session_id=session_id or str(uuid4()),
        source_text=source_text,
        source_language=source,
        target_language=target,
        translated_output=translated_text,
        confidence_score=confidence_score,
        escalation_flag=escalation_flag,
        escalation_reason=escalation_reason,
        latency_ms=latency_ms,
        model_name=translator.model_name,
        clinician_id=clinician_id,
    )

    return {
        "session_id": log_record["session_id"],
        "timestamp": log_record["timestamp"],
        "translated_text": log_record["translated_output"],
        "confidence_score": log_record["confidence_score"],
        "escalation_flag": log_record["escalation_flag"],
        "escalation_reason": log_record["escalation_reason"],
        "model_name": log_record["model_name"],
    }
