
from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.services.ai.inference import SMaLL100Translator 


def __getattr__(name: str):
    """Lazy import to avoid loading torch at package import time."""
    if name == "SMaLL100Translator":
        from app.services.ai.inference import SMaLL100Translator
        return SMaLL100Translator
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


__all__ = ["SMaLL100Translator"]
