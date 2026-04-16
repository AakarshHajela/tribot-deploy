'''Model Loader, responsible for loading the SMaLL-100 model and tokenizer from HuggingFace or local paths.
Load tokenizer and device selection'''

from __future__ import annotations

import logging
from pathlib import Path

import torch
from transformers import M2M100ForConditionalGeneration

from app.services.ai.tokenization_small100 import SMALL100Tokenizer

logger = logging.getLogger(__name__)


def detect_device(preference: str = "auto") -> torch.device:
    '''
        Detect the appropriate torch device based on user preference and availability.
    '''
    if preference == "cuda":
        if not torch.cuda.is_available():
            logger.warning("CUDA requested but not available — falling back to CPU.")
            return torch.device("cpu")
        return torch.device("cuda")
    if preference == "cpu":
        return torch.device("cpu")
    # auto
    return torch.device("cuda" if torch.cuda.is_available() else "cpu")


def load_tokenizer(model_name_or_path: str) -> SMALL100Tokenizer:
    """
    Load the SMALL100Tokenizer

    Args:
        model_name_or_path: HuggingFace model identifier (e.g.
            ``"alirezamsh/small100"``) or path to a local directory
            containing tokenizer files.

    Returns:
        An initialised :class:`SMALL100Tokenizer`.
    """
    path = Path(model_name_or_path)
    if path.exists() and path.is_dir():
        required = ["vocab.json", "sentencepiece.bpe.model"]
        for fname in required:
            if not (path / fname).exists():
                raise FileNotFoundError(
                    f"Tokenizer file '{fname}' not found in {model_name_or_path}. "
                    f"Required files: {required}"
                )

    try:
        tokenizer = SMALL100Tokenizer.from_pretrained(model_name_or_path)
        logger.info("Tokenizer loaded from '%s'.", model_name_or_path)
        return tokenizer
    except Exception as exc:
        raise RuntimeError(
            f"Failed to load SMALL100Tokenizer from '{model_name_or_path}'. "
            f"Ensure the model path is correct and contains the required files. "
            f"Original error: {exc}"
        ) from exc


def load_model(
    model_name_or_path: str,
    device: torch.device | None = None,
) -> M2M100ForConditionalGeneration:
    """
    Load the M2M100ForConditionalGeneration model (SMaLL-100 weights).

    Args:
        model_name_or_path: HuggingFace hub identifier or local path.
        device: Target device. If ``None``, auto-detects.

    Returns:
        The loaded model placed on the target device in eval mode.
    """
    if device is None:
        device = detect_device()

    path = Path(model_name_or_path)
    if path.exists() and path.is_dir():
        required_patterns = ["config.json"]
        for fname in required_patterns:
            if not (path / fname).exists():
                raise FileNotFoundError(
                    f"Model file '{fname}' not found in {model_name_or_path}. "
                    f"Ensure this directory contains the SMaLL-100 model files."
                )

    try:
        model = M2M100ForConditionalGeneration.from_pretrained(model_name_or_path)
        model = model.to(device)
        model.eval()
        logger.info(
            "Model loaded from '%s' on device '%s'.",
            model_name_or_path,
            device,
        )
        return model
    except Exception as exc:
        raise RuntimeError(
            f"Failed to load SMaLL-100 model from '{model_name_or_path}'. "
            f"Ensure the path is correct and contains valid model weights. "
            f"Original error: {exc}"
        ) from exc
