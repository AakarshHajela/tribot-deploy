"""
Preprocessing for English and Arabic medical text.

Handles Unicode normalization, Arabic-specific normalization (tatweel,
diacritics, alef/yaa variants), English quote/dash normalization, and
whitespace/punctuation cleanup.
"""

from __future__ import annotations

import re
import unicodedata


# ---------------------------------------------------------------------------
# Arabic normalization helpers
# ---------------------------------------------------------------------------

# Tatweel / kashida
_TATWEEL = "\u0640"

# Arabic diacritics (tashkeel): two sub-ranges that avoid Arabic base letters
# U+0610–U+061A: Arabic signs above/below
# U+064B–U+065F: Fathatan through Hamza below
_ARABIC_DIACRITICS_RE = re.compile(r"[\u0610-\u061A\u064B-\u065F]")

# Alef variants → plain alef (ا)
_ALEF_VARIANTS_RE = re.compile(r"[\u0622\u0623\u0625\u0671]")  # آ أ إ ٱ

# Final-yaa normalisation: ى → ي
_ALEF_MAKSURA = "\u0649"  # ى
_YAA = "\u064A"           # ي


def _normalize_arabic(text: str) -> str:
    """Apply Arabic-specific normalization rules."""
    # Remove tatweel
    text = text.replace(_TATWEEL, "")
    # Remove diacritics
    text = _ARABIC_DIACRITICS_RE.sub("", text)
    # Normalize alef variants → ا
    text = _ALEF_VARIANTS_RE.sub("\u0627", text)
    # Normalize alef maksura → yaa
    text = text.replace(_ALEF_MAKSURA, _YAA)
    return text


# ---------------------------------------------------------------------------
# English normalization helpers
# ---------------------------------------------------------------------------

# Smart quotes → ASCII
_SMART_SINGLE_QUOTES_RE = re.compile(r"[\u2018\u2019\u201A\u201B]")
_SMART_DOUBLE_QUOTES_RE = re.compile(r"[\u201C\u201D\u201E\u201F]")

# En-dash / em-dash → hyphen-minus
_DASHES_RE = re.compile(r"[\u2013\u2014]")


def _normalize_english(text: str) -> str:
    """Normalize English smart quotes and dashes to ASCII equivalents."""
    text = _SMART_SINGLE_QUOTES_RE.sub("'", text)
    text = _SMART_DOUBLE_QUOTES_RE.sub('"', text)
    text = _DASHES_RE.sub("-", text)
    return text


# ---------------------------------------------------------------------------
# Shared cleanup
# ---------------------------------------------------------------------------

# Multiple whitespace → single space
_MULTI_SPACE_RE = re.compile(r"\s+")

# Ensure no space before common punctuation, one space after
_PUNCT_SPACING_RE = re.compile(r"\s*([,;:!?.])\s*")


def _cleanup(text: str) -> str:
    """Normalize whitespace and fix punctuation spacing."""
    text = _MULTI_SPACE_RE.sub(" ", text)
    text = _PUNCT_SPACING_RE.sub(r"\1 ", text)
    return text.strip()


def preprocess(text: str, lang: str) -> str:
    """
    Preprocess input text before feeding it to the translation model.

    Args:
        text: Raw input text.
        lang: Language code — ``"en"`` or ``"ar"``.

    Returns:
        Cleaned text ready for tokenization.
    """
    if not text or not text.strip():
        return ""

    # Unicode NFC normalization
    text = unicodedata.normalize("NFC", text)

    # Language-specific normalization
    lang_lower = lang.strip().lower()
    if lang_lower == "ar":
        text = _normalize_arabic(text)
    elif lang_lower == "en":
        text = _normalize_english(text)

    text = _cleanup(text)

    return text
