from __future__ import annotations

import logging
import re
from typing import List, Tuple

import torch

from app.services.ai.model_loader import detect_device, load_model, load_tokenizer
from app.services.ai.preprocessing import preprocess
from app.services.ai.tokenization_small100 import SMALL100Tokenizer

logger = logging.getLogger(__name__)

# Regex to extract all digit sequences (used for sanity checks)
_DIGIT_RE = re.compile(r"\d+")


class SMaLL100Translator:
    """
    SMaLL-100 translator class that loads the model and tokenizer, and translation functionality.

    Usage::

        translator = SMaLL100Translator(model_path="alirezamsh/small100")
        translator.load()  # optional — happens lazily on first translate()
        translated, confidence, red_flags = translator.translate(
            "chest pain", "en", "ar"
        )
    Args:
        model_path: HuggingFace model identifier or local directory path.
        device: ``"auto"``, ``"cpu"``, or ``"cuda"``.
        num_beams: Number of beams for beam search during generation.
        max_new_tokens: Maximum number of new tokens to generate.
    """

    model_name: str = "small100-nmt"

    def __init__(
        self,
        model_path: str = "alirezamsh/small100",
        device: str = "auto",
        num_beams: int = 4,
        max_new_tokens: int = 256,
    ) -> None:
        self._model_path = model_path
        self._device_pref = device
        self._num_beams = num_beams
        self._max_new_tokens = max_new_tokens

        self._model = None
        self._tokenizer: SMALL100Tokenizer | None = None
        self._device: torch.device | None = None

    @property
    def is_loaded(self) -> bool:
        """Return ``True`` if model and tokenizer are loaded."""
        return self._model is not None and self._tokenizer is not None

    def load(self) -> None:
        if self.is_loaded:
            return

        logger.info("Loading SMaLL-100 model from '%s' …", self._model_path)
        self._device = detect_device(self._device_pref)
        self._tokenizer = load_tokenizer(self._model_path)
        self._model = load_model(self._model_path, self._device)
        logger.info("SMaLL-100 model ready on %s.", self._device)

    def translate(
        self,
        text: str,
        source_language: str,
        target_language: str,
    ) -> Tuple[str, float, List[str]]:
        """
        Translate text from *source_language* to *target_language*.

        Args:
            text: Input text to translate.
            source_language: Source language code (``"en"`` or ``"ar"``).
            target_language: Target language code (``"en"`` or ``"ar"``).

        Returns:
            A 3-tuple of ``(translated_text, confidence_score, issues)``.

            - *translated_text*: The generated translation.
            - *confidence_score*: Heuristic confidence (fixed at 85.0 for
              V1 since we have no separate confidence model).
            - *issues*: A list of issue strings found by sanity checks
              (e.g. ``"empty_output"``, ``"digit_mismatch"``).
        """
        # Ensure model is loaded
        if not self.is_loaded:
            self.load()

        # 1. Pre-process
        clean_text = preprocess(text, source_language)
        if not clean_text:
            return "", 0.0, ["empty_input"]

        # 2. Set target language on tokenizer
        self._tokenizer.tgt_lang = target_language

        # 3. Tokenize
        encoded = self._tokenizer(
            clean_text,
            return_tensors="pt",
            max_length=512,
            truncation=True,
        )
        input_ids = encoded["input_ids"].to(self._device)
        attention_mask = encoded["attention_mask"].to(self._device)

        # 4. Generate
        with torch.no_grad():
            generated_ids = self._model.generate(
                input_ids=input_ids,
                attention_mask=attention_mask,
                forced_bos_token_id=self._tokenizer.get_lang_id(target_language),
                num_beams=self._num_beams,
                max_new_tokens=self._max_new_tokens,
            )

        # 5. Decode
        raw_output = self._tokenizer.batch_decode(
            generated_ids, skip_special_tokens=True
        )[0]

        # 6. Post-process
        translated_text = _postprocess(raw_output)

        # 7. Sanity checks
        issues = _sanity_checks(clean_text, translated_text)

        # 8. Confidence — fixed heuristic for V1
        confidence = 85.0
        if "empty_output" in issues:
            confidence = 0.0
        elif "digit_mismatch" in issues:
            confidence = 65.0

        return translated_text, confidence, issues


# ------------------------------------------------------------------
# Post-processing & sanity checks
# ------------------------------------------------------------------

def _postprocess(text: str) -> str:
    """Basic post-processing of model output."""
    # Strip leading/trailing whitespace
    text = text.strip()
    # Collapse multiple spaces
    text = re.sub(r"\s+", " ", text)
    return text


def _sanity_checks(source: str, output: str) -> List[str]:
    """
    Run basic sanity checks on the translation output.

    Returns:
        List of issue identifiers (empty list means all checks passed).
    """
    issues: List[str] = []

    # Empty output check
    if not output or not output.strip():
        issues.append("empty_output")
        return issues

    # Digit mismatch check — compare sorted digit sequences
    src_digits = sorted(_DIGIT_RE.findall(source))
    out_digits = sorted(_DIGIT_RE.findall(output))
    if src_digits != out_digits:
        issues.append("digit_mismatch")

    return issues
