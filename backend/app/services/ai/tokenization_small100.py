import json
import os
from pathlib import Path
from shutil import copyfile
from typing import Any, Dict, List, Optional, Tuple, Union

import sentencepiece

from transformers.tokenization_utils import BatchEncoding, PreTrainedTokenizer
from transformers.utils import logging


logger = logging.get_logger(__name__)

SPIECE_UNDERLINE = "▁"

VOCAB_FILES_NAMES = {
    "vocab_file": "vocab.json",
    "spm_file": "sentencepiece.bpe.model",
    "tokenizer_config_file": "tokenizer_config.json",
}

PRETRAINED_VOCAB_FILES_MAP = {
    "vocab_file": {
        "alirezamsh/small100": "https://huggingface.co/alirezamsh/small100/resolve/main/vocab.json",
    },
    "spm_file": {
        "alirezamsh/small100": "https://huggingface.co/alirezamsh/small100/resolve/main/sentencepiece.bpe.model",
    },
    "tokenizer_config_file": {
        "alirezamsh/small100": "https://huggingface.co/alirezamsh/small100/resolve/main/tokenizer_config.json",
    },
}

PRETRAINED_POSITIONAL_EMBEDDINGS_SIZES = {
    "alirezamsh/small100": 1024,
}

# fmt: off
FAIRSEQ_LANGUAGE_CODES = {
    "m2m100": ["af", "am", "ar", "ast", "az", "ba", "be", "bg", "bn", "br", "bs", "ca", "ceb", "cs", "cy", "da", "de", "el", "en", "es", "et", "fa", "ff", "fi", "fr", "fy", "ga", "gd", "gl", "gu", "ha", "he", "hi", "hr", "ht", "hu", "hy", "id", "ig", "ilo", "is", "it", "ja", "jv", "ka", "kk", "km", "kn", "ko", "lb", "lg", "ln", "lo", "lt", "lv", "mg", "mk", "ml", "mn", "mr", "ms", "my", "ne", "nl", "no", "ns", "oc", "or", "pa", "pl", "ps", "pt", "ro", "ru", "sd", "si", "sk", "sl", "so", "sq", "sr", "ss", "su", "sv", "sw", "ta", "th", "tl", "tn", "tr", "uk", "ur", "uz", "vi", "wo", "xh", "yi", "yo", "zh", "zu"]
}
# fmt: on


class SMALL100Tokenizer(PreTrainedTokenizer):
    """
    Construct an SMALL100 tokenizer. Based on `SentencePiece`_.

    This tokenizer inherits from :class:`~transformers.PreTrainedTokenizer`
    which contains most of the main methods.

    Args:
        vocab_file: Path to the vocabulary file.
        spm_file: Path to SentencePiece model file.
        tgt_lang: Target language code (e.g. ``"ar"``).
    """

    vocab_files_names = VOCAB_FILES_NAMES
    max_model_input_sizes = PRETRAINED_POSITIONAL_EMBEDDINGS_SIZES
    pretrained_vocab_files_map = PRETRAINED_VOCAB_FILES_MAP
    model_input_names = ["input_ids", "attention_mask"]

    prefix_tokens: List[int] = []
    suffix_tokens: List[int] = []

    def __init__(
        self,
        vocab_file,
        spm_file,
        tgt_lang=None,
        bos_token="<s>",
        eos_token="</s>",
        sep_token="</s>",
        pad_token="<pad>",
        unk_token="<unk>",
        language_codes="m2m100",
        sp_model_kwargs: Optional[Dict[str, Any]] = None,
        num_madeup_words=8,
        **kwargs,
    ) -> None:
        self.sp_model_kwargs = {} if sp_model_kwargs is None else sp_model_kwargs

        self.language_codes = language_codes
        fairseq_language_code = FAIRSEQ_LANGUAGE_CODES[language_codes]
        self.lang_code_to_token = {
            lang_code: f"__{lang_code}__" for lang_code in fairseq_language_code
        }

        kwargs["additional_special_tokens"] = kwargs.get("additional_special_tokens", [])
        kwargs["additional_special_tokens"] += [
            self.get_lang_token(lang_code)
            for lang_code in fairseq_language_code
            if self.get_lang_token(lang_code) not in kwargs["additional_special_tokens"]
        ]

        self.vocab_file = vocab_file
        self.encoder = load_json(vocab_file)
        self.decoder = {v: k for k, v in self.encoder.items()}

        self.spm_file = spm_file
        self.sp_model = load_spm(spm_file, self.sp_model_kwargs)

        self.encoder_size = len(self.encoder)

        self.lang_token_to_id = {
            self.get_lang_token(lang_code): self.encoder_size + i
            for i, lang_code in enumerate(fairseq_language_code)
        }
        self.lang_code_to_id = {
            lang_code: self.encoder_size + i
            for i, lang_code in enumerate(fairseq_language_code)
        }
        self.id_to_lang_token = {v: k for k, v in self.lang_token_to_id.items()}

        self._tgt_lang = tgt_lang if tgt_lang is not None else "en"
        self.cur_lang_id = self.get_lang_id(self._tgt_lang)
        self.num_madeup_words = num_madeup_words

        super().__init__(
            tgt_lang=tgt_lang,
            bos_token=bos_token,
            eos_token=eos_token,
            sep_token=sep_token,
            unk_token=unk_token,
            pad_token=pad_token,
            language_codes=language_codes,
            sp_model_kwargs=self.sp_model_kwargs,
            num_madeup_words=num_madeup_words,
            **kwargs,
        )

        self.set_lang_special_tokens(self._tgt_lang)

    @property
    def vocab_size(self) -> int:
        return len(self.encoder) + len(self.lang_token_to_id) + self.num_madeup_words

    @property
    def tgt_lang(self) -> str:
        return self._tgt_lang

    @tgt_lang.setter
    def tgt_lang(self, new_tgt_lang: str) -> None:
        self._tgt_lang = new_tgt_lang
        self.set_lang_special_tokens(self._tgt_lang)

    def _tokenize(self, text: str) -> List[str]:
        return self.sp_model.encode(text, out_type=str)

    def _convert_token_to_id(self, token):
        if token in self.lang_token_to_id:
            return self.lang_token_to_id[token]
        return self.encoder.get(token, self.encoder[self.unk_token])

    def _convert_id_to_token(self, index: int) -> str:
        """Converts an index (integer) in a token (str) using the decoder."""
        if index in self.id_to_lang_token:
            return self.id_to_lang_token[index]
        return self.decoder.get(index, self.unk_token)

    def convert_tokens_to_string(self, tokens: List[str]) -> str:
        """Converts a sequence of tokens (strings for sub-words) in a single string."""
        return self.sp_model.decode(tokens)

    def get_special_tokens_mask(
        self,
        token_ids_0: List[int],
        token_ids_1: Optional[List[int]] = None,
        already_has_special_tokens: bool = False,
    ) -> List[int]:
        if already_has_special_tokens:
            return super().get_special_tokens_mask(
                token_ids_0=token_ids_0,
                token_ids_1=token_ids_1,
                already_has_special_tokens=True,
            )

        prefix_ones = [1] * len(self.prefix_tokens)
        suffix_ones = [1] * len(self.suffix_tokens)
        if token_ids_1 is None:
            return prefix_ones + ([0] * len(token_ids_0)) + suffix_ones
        return prefix_ones + ([0] * len(token_ids_0)) + ([0] * len(token_ids_1)) + suffix_ones

    def build_inputs_with_special_tokens(
        self, token_ids_0: List[int], token_ids_1: Optional[List[int]] = None
    ) -> List[int]:
        if token_ids_1 is None:
            if self.prefix_tokens is None:
                return token_ids_0 + self.suffix_tokens
            else:
                return self.prefix_tokens + token_ids_0 + self.suffix_tokens
        if self.prefix_tokens is None:
            return token_ids_0 + token_ids_1 + self.suffix_tokens
        else:
            return self.prefix_tokens + token_ids_0 + token_ids_1 + self.suffix_tokens

    def get_vocab(self) -> Dict:
        vocab = {self.convert_ids_to_tokens(i): i for i in range(self.vocab_size)}
        vocab.update(self.added_tokens_encoder)
        return vocab

    def __getstate__(self) -> Dict:
        state = self.__dict__.copy()
        state["sp_model"] = None
        return state

    def __setstate__(self, d: Dict) -> None:
        self.__dict__ = d

        # for backward compatibility
        if not hasattr(self, "sp_model_kwargs"):
            self.sp_model_kwargs = {}

        self.sp_model = load_spm(self.spm_file, self.sp_model_kwargs)

    def save_vocabulary(
        self, save_directory: str, filename_prefix: Optional[str] = None
    ) -> Tuple[str]:
        save_dir = Path(save_directory)
        if not save_dir.is_dir():
            raise OSError(f"{save_directory} should be a directory")
        vocab_save_path = save_dir / (
            (filename_prefix + "-" if filename_prefix else "") + self.vocab_files_names["vocab_file"]
        )
        spm_save_path = save_dir / (
            (filename_prefix + "-" if filename_prefix else "") + self.vocab_files_names["spm_file"]
        )

        save_json(self.encoder, vocab_save_path)

        if (
            os.path.abspath(self.spm_file) != os.path.abspath(spm_save_path)
            and os.path.isfile(self.spm_file)
        ):
            copyfile(self.spm_file, spm_save_path)
        elif not os.path.isfile(self.spm_file):
            with open(spm_save_path, "wb") as fi:
                content_spiece_model = self.sp_model.serialized_model_proto()
                fi.write(content_spiece_model)

        return (str(vocab_save_path), str(spm_save_path))

    def prepare_seq2seq_batch(
        self,
        src_texts: List[str],
        tgt_texts: Optional[List[str]] = None,
        tgt_lang: str = "ro",
        **kwargs,
    ) -> BatchEncoding:
        self.tgt_lang = tgt_lang
        self.set_lang_special_tokens(self.tgt_lang)
        return super().prepare_seq2seq_batch(src_texts, tgt_texts, **kwargs)

    def _build_translation_inputs(
        self, raw_inputs, tgt_lang: Optional[str], **extra_kwargs
    ):
        """Used by translation pipeline, to prepare inputs for the generate function."""
        if tgt_lang is None:
            raise ValueError("Translation requires a `tgt_lang` for this model")
        self.tgt_lang = tgt_lang
        inputs = self(raw_inputs, add_special_tokens=True, **extra_kwargs)
        return inputs

    def _switch_to_input_mode(self):
        self.set_lang_special_tokens(self.tgt_lang)

    def _switch_to_target_mode(self):
        self.prefix_tokens = None
        self.suffix_tokens = [self.eos_token_id]

    def set_lang_special_tokens(self, src_lang: str) -> None:
        """Reset the special tokens to the tgt lang setting.

        No prefix and suffix=[eos, tgt_lang_code].
        """
        lang_token = self.get_lang_token(src_lang)
        self.cur_lang_id = self.lang_token_to_id[lang_token]
        self.prefix_tokens = [self.cur_lang_id]
        self.suffix_tokens = [self.eos_token_id]

    def get_lang_token(self, lang: str) -> str:
        return self.lang_code_to_token[lang]

    def get_lang_id(self, lang: str) -> int:
        lang_token = self.get_lang_token(lang)
        return self.lang_token_to_id[lang_token]


def load_spm(path: str, sp_model_kwargs: Dict[str, Any]) -> sentencepiece.SentencePieceProcessor:
    spm = sentencepiece.SentencePieceProcessor(**sp_model_kwargs)
    spm.Load(str(path))
    return spm


def load_json(path: str) -> Union[Dict, List]:
    with open(path, "r") as f:
        return json.load(f)


def save_json(data, path: str) -> None:
    with open(path, "w") as f:
        json.dump(data, f, indent=2)
