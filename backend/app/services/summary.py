from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger(__name__)

_model_cache: dict[str, Any] = {}


def _get_model(model_path: str) -> dict:
    if model_path not in _model_cache:
        from transformers import AutoModelForSeq2SeqLM, AutoTokenizer
        import torch

        logger.info("Loading summary model '%s' …", model_path)
        tokenizer = AutoTokenizer.from_pretrained(model_path)

        device = (
            "mps" if torch.backends.mps.is_available()
            else "cuda" if torch.cuda.is_available()
            else "cpu"
        )
        model = AutoModelForSeq2SeqLM.from_pretrained(
            model_path,
            torch_dtype=torch.float16 if device != "cpu" else torch.float32,
        )
        model = model.to(device)
        model.eval()
        _model_cache[model_path] = {"tokenizer": tokenizer, "model": model, "device": device}
        logger.info("Summary model ready on %s.", device)
    return _model_cache[model_path]


ATS_LABELS = {
    1: "Category 1 – Resuscitation (Immediate / life threat)",
    2: "Category 2 – Emergency (Within 10 minutes)",
    3: "Category 3 – Urgent (Within 30 minutes)",
    4: "Category 4 – Semi-urgent (Within 60 minutes)",
    5: "Category 5 – Non-urgent (Within 120 minutes)",
}


def _norm_lang(code: str | None) -> str:
    if not code:
        return ""
    v = str(code).strip().lower()
    if v in {"english", "en"}:
        return "en"
    if v in {"arabic", "ar"}:
        return "ar"
    return v


def _patient_line_english(m: dict) -> str:
    """English text for charting: follows triage convention (source = utterance, target = translation)."""
    src = _norm_lang(m.get("source_language"))
    tgt = _norm_lang(m.get("target_language"))
    orig = (m.get("original_text") or "").strip()
    trans = (m.get("translated_text") or "").strip()
    if tgt == "en":
        return trans
    if src == "en":
        return orig
    return trans or orig


def _format_vitals(session: dict) -> str:
    parts: list[str] = []
    if session.get("bp_systolic"):
        parts.append(f"BP {session['bp_systolic']}/{session['bp_diastolic']} mmHg")
    if session.get("heart_rate"):
        parts.append(f"HR {session['heart_rate']} bpm")
    if session.get("temperature"):
        parts.append(f"Temp {session['temperature']}°F")
    if session.get("respiratory_rate"):
        parts.append(f"RR {session['respiratory_rate']} br/min")
    if session.get("spo2"):
        parts.append(f"SpO2 {session['spo2']}%")
    return ", ".join(parts) if parts else "not recorded"


def _rule_based_summary(session: dict, patient: dict, messages: list[dict]) -> str:
    """Accurate, deterministic narrative summary built directly from session data."""
    name = patient.get("full_name", "The patient")
    mrn = patient.get("mrn", "N/A")
    lang = "Arabic" if patient.get("patient_language") == "ar" else "English"
    ats = session.get("ats_category")
    ats_label = ATS_LABELS.get(ats, "not yet assigned") if ats else "not yet assigned"
    nurse_confirmed = session.get("nurse_confirmed_ats", False)

    patient_msgs: list[str] = []
    for m in messages:
        if m.get("sender") != "patient":
            continue
        line = _patient_line_english(m)
        if line:
            patient_msgs.append(line)
    chief_complaint = patient_msgs[0] if patient_msgs else None
    additional = patient_msgs[1:] if len(patient_msgs) > 1 else []

    complaint_str = (
        f", presenting with {chief_complaint.lower().rstrip('.')}"
        if chief_complaint else ""
    )
    sentences: list[str] = [
        f"{name} (MRN: {mrn}), an {lang}-speaking patient, attended the emergency department"
        f"{complaint_str}."
    ]

    if additional:
        sentences.append(
            "The patient further reported: " + "; ".join(s.rstrip(".") for s in additional) + "."
        )

    vitals = _format_vitals(session)
    if vitals != "not recorded":
        sentences.append(f"Vital signs on presentation were {vitals}.")
    else:
        sentences.append("Vital signs were not recorded at the time of this report.")

    confirmed_clause = ", confirmed by nursing staff" if nurse_confirmed else ""
    sentences.append(f"The patient was triaged as ATS {ats_label}{confirmed_clause}.")

    dur_sec = session.get("duration_seconds")
    avg_conf = session.get("avg_translation_confidence")
    stats_parts: list[str] = []
    if dur_sec:
        stats_parts.append(f"session duration {dur_sec // 60} min {dur_sec % 60:02d} sec")
    if avg_conf is not None:
        stats_parts.append(f"average translation confidence {avg_conf:.1f}%")
    if stats_parts:
        sentences.append("The encounter recorded a " + " and ".join(stats_parts) + ".")

    return " ".join(sentences)


def _build_rephrase_prompt(base_summary: str) -> str:
    """
    Give flan-t5 a complete, accurate paragraph to polish rather than
    asking it to interpret raw structured data (which causes hallucinations).
    """
    return (
        "Rewrite the following clinical triage note in clear, professional medical language. "
        "The entire note must be in English only. "
        "Keep all facts exactly as stated. Do not add or remove any information. "
        "Use formal prose suitable for a hospital record:\n\n"
        f"{base_summary}"
    )


def _is_acceptable(output: str, base: str) -> bool:
    """
    Reject the AI output if it is essentially echoing the prompt
    or is too short to be a meaningful summary.
    """
    if len(output.split()) < 20:
        return False

    # Measure word overlap — if >85% of output words appear in the base,
    # the model is just copying rather than rephrasing.
    base_words = set(base.lower().split())
    output_words = output.lower().split()
    if not output_words:
        return False
    overlap = sum(1 for w in output_words if w in base_words) / len(output_words)
    if overlap > 0.85:
        return False

    return True


def generate_summary(
    session: dict,
    patient: dict,
    messages: list[dict],
    *,
    model_path: str = "google/flan-t5-base",
    use_ai: bool = True,
    max_new_tokens: int = 300,
    **_kwargs: Any,
) -> tuple[str, bool]:
    """
    Generate a clinical triage summary.

    Strategy (when use_ai=True):
      1. Build an accurate rule-based summary from the session data.
      2. Ask flan-t5 to rephrase it into polished clinical prose.
      3. Validate the output — if it echoes the input or is too short, use the
         rule-based summary instead.

    Returns (summary_text, ai_was_used).
    """
    base = _rule_based_summary(session, patient, messages)

    if not use_ai:
        return base, False

    try:
        import torch

        cache = _get_model(model_path)
        tokenizer = cache["tokenizer"]
        model = cache["model"]
        device = cache["device"]

        prompt = _build_rephrase_prompt(base)
        inputs = tokenizer(
            prompt,
            return_tensors="pt",
            max_length=512,
            truncation=True,
            padding=False,
        ).to(device)

        with torch.no_grad():
            output_ids = model.generate(
                **inputs,
                max_new_tokens=200,
                num_beams=4,
                early_stopping=True,
                no_repeat_ngram_size=3,
                length_penalty=1.5,
                min_length=40,
            )

        output = tokenizer.decode(output_ids[0], skip_special_tokens=True).strip()

        if _is_acceptable(output, base):
            return output, True

        logger.info("flan-t5 output rejected (echoing / too short) — using rule-based summary.")
        return base, True

    except Exception as exc:
        logger.warning("Summary model failed (%s) — using rule-based fallback.", exc)
        return base, False
