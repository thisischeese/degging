from __future__ import annotations

import os
from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path
from typing import Any
from uuid import UUID

from app.models.query_preprocess import QueryPreprocessData

_MENU_NER_TOKENIZER_NAME = "KPF/KPF-bert-ner"
_MENU_NER_MODEL_DIR = "food_ner_model"
# Official KPF label order maps CV_FOOD to B/I indices below.
_MENU_NER_FOOD_LABEL_IDS = frozenset({28, 178})


def _resolve_menu_ner_model_path() -> Path:
    return Path(__file__).resolve().parents[2] / _MENU_NER_MODEL_DIR


def _import_menu_ner_libraries() -> tuple[Any, Any, Any]:
    try:
        import torch
    except ImportError as exc:
        raise RuntimeError(
            "PyTorch is required to run menu phrase extraction."
        ) from exc

    try:
        from transformers import AutoTokenizer, BertForTokenClassification
    except ImportError as exc:
        raise RuntimeError(
            "transformers is required to run menu phrase extraction."
        ) from exc

    return AutoTokenizer, BertForTokenClassification, torch


def _to_list(value: Any) -> Any:
    if hasattr(value, "tolist"):
        return value.tolist()
    return value


def _collect_food_phrases(
    query: str,
    predicted_ids: list[int],
    offset_mapping: list[list[int] | tuple[int, int]],
    special_tokens_mask: list[int],
) -> list[str]:
    phrases: list[str] = []
    span_start: int | None = None
    span_end: int | None = None

    def flush_span() -> None:
        nonlocal span_start, span_end
        if span_start is None or span_end is None:
            span_start = None
            span_end = None
            return

        phrase = query[span_start:span_end].strip()
        if phrase:
            phrases.append(phrase)

        span_start = None
        span_end = None

    for label_id, offsets, is_special in zip(
        predicted_ids,
        offset_mapping,
        special_tokens_mask,
    ):
        start = int(offsets[0])
        end = int(offsets[1])

        if is_special or end <= start or label_id not in _MENU_NER_FOOD_LABEL_IDS:
            flush_span()
            continue

        if span_start is None or span_end is None:
            span_start = start
            span_end = end
            continue

        if start <= span_end:
            span_end = max(span_end, end)
            continue

        if query[span_end:start].isspace():
            span_end = end
            continue

        flush_span()
        span_start = start
        span_end = end

    flush_span()
    return phrases


def _load_local_menu_ner_components(
    model_path: Path,
    AutoTokenizer: Any,
    BertForTokenClassification: Any,
) -> tuple[Any, Any]:
    tokenizer = AutoTokenizer.from_pretrained(
        str(model_path),
        local_files_only=True,
    )
    model = BertForTokenClassification.from_pretrained(
        str(model_path),
        local_files_only=True,
    )
    return tokenizer, model


def _download_menu_ner_components(
    model_path: Path,
    hf_token: str | None,
    AutoTokenizer: Any,
    BertForTokenClassification: Any,
) -> None:
    model_path.mkdir(parents=True, exist_ok=True)

    try:
        tokenizer = AutoTokenizer.from_pretrained(
            _MENU_NER_TOKENIZER_NAME,
            token=hf_token,
        )
        model = BertForTokenClassification.from_pretrained(
            _MENU_NER_TOKENIZER_NAME,
            token=hf_token,
        )
    except Exception as exc:
        raise RuntimeError(
            f"Failed to download menu NER components from '{_MENU_NER_TOKENIZER_NAME}': {exc}"
        ) from exc

    tokenizer.save_pretrained(str(model_path))
    model.save_pretrained(str(model_path))


@lru_cache(maxsize=1)
def _load_menu_ner_components() -> tuple[Any, Any, Any]:
    model_path = _resolve_menu_ner_model_path()
    AutoTokenizer, BertForTokenClassification, torch = _import_menu_ner_libraries()
    hf_token = os.getenv("HF_TOKEN")

    try:
        tokenizer, model = _load_local_menu_ner_components(
            model_path,
            AutoTokenizer,
            BertForTokenClassification,
        )
    except Exception:
        _download_menu_ner_components(
            model_path,
            hf_token,
            AutoTokenizer,
            BertForTokenClassification,
        )
        try:
            tokenizer, model = _load_local_menu_ner_components(
                model_path,
                AutoTokenizer,
                BertForTokenClassification,
            )
        except Exception as exc:
            raise RuntimeError(
                f"Failed to load menu NER components from '{model_path}': {exc}"
            ) from exc

    if hasattr(model, "to"):
        model.to("cpu")
    model.eval()

    return tokenizer, model, torch


@dataclass(slots=True)
class PreprocessedQuery:
    normalized_query: str
    vector: list[float] = field(default_factory=list)
    menu_phrases: list[str] = field(default_factory=list)


class QueryPreprocessService:
    async def encode_query(self, query: str) -> list[float]:
        """
        Encode the incoming query text into a vector.
        The encoder integration is intentionally stubbed until the model is ready.
        """
        # encoder_client = get_query_encoder()
        # return await encoder_client.encode(query)
        return []

    async def extract_menu_phrases(self, query: str) -> list[str]:
        normalized_query = query.strip()
        if not normalized_query:
            return []

        tokenizer, model, torch = _load_menu_ner_components()
        encoded_inputs = tokenizer(
            normalized_query,
            return_tensors="pt",
            return_offsets_mapping=True,
            return_special_tokens_mask=True,
            truncation=True,
            max_length=512,
        )
        offset_mapping = _to_list(encoded_inputs.pop("offset_mapping")[0])
        special_tokens_mask = _to_list(encoded_inputs.pop("special_tokens_mask")[0])

        with torch.no_grad():
            outputs = model(**encoded_inputs)

        logits = outputs.logits if hasattr(outputs, "logits") else outputs[0]
        predicted_ids = _to_list(logits.argmax(dim=-1)[0])

        return _collect_food_phrases(
            normalized_query,
            [int(label_id) for label_id in predicted_ids],
            offset_mapping,
            special_tokens_mask,
        )

    async def preprocess(self, query: str) -> PreprocessedQuery:
        normalized_query = query.strip()
        vector = await self.encode_query(normalized_query)
        menu_phrases = await self.extract_menu_phrases(normalized_query)
        return PreprocessedQuery(
            normalized_query=normalized_query,
            vector=vector,
            menu_phrases=menu_phrases,
        )

    async def preprocess_query(self, query: str, user_id: UUID) -> QueryPreprocessData:
        """
        Return the public preprocess response payload.
        The current endpoint keeps returning empty extracted menus until menu resolution
        can be grounded with search candidates.
        """
        _ = user_id
        processed_query = await self.preprocess(query)

        return QueryPreprocessData(
            original_query=processed_query.normalized_query,
            vector=processed_query.vector,
            dimensions=len(processed_query.vector),
            extracted_menus={},
        )
