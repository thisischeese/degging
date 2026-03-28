from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
import logging
import os
import pickle
from pathlib import Path
import re
from typing import Any

import numpy as np
from sklearn.decomposition import TruncatedSVD
from sklearn.preprocessing import normalize

from app.services.vibe_tags import resolve_vibe_labels

logger = logging.getLogger("uvicorn.error")

_MENU_QUERY_ENCODER_FILENAME = "menu_query_encoder.pkl"
_MENU_QUERY_MODEL_NAME = "BM-K/KoSimCSE-roberta-multitask"
_MENU_QUERY_MODEL_DIR = "bm_k_kosimcse_roberta_multitask"
_MENU_QUERY_VECTOR_DIMENSIONS = 64
_MENU_QUERY_BATCH_SIZE = 32
_MENU_SEARCH_TEXT_SOURCE = "menu_name+menu_description"
_MENU_VECTOR_TEXT_SOURCE = "menu_name+menu_description+vibe_tags"


@dataclass(slots=True)
class MenuQueryEncoderArtifact:
    projection: Any
    artifact_path: Path
    target_dim: int = _MENU_QUERY_VECTOR_DIMENSIONS
    model_name: str = _MENU_QUERY_MODEL_NAME
    search_text_source: str = _MENU_SEARCH_TEXT_SOURCE
    vector_text_source: str = _MENU_VECTOR_TEXT_SOURCE


def _project_root() -> Path:
    return Path(__file__).resolve().parents[2]


def resolve_menu_query_encoder_path() -> Path:
    return _project_root() / "models" / _MENU_QUERY_ENCODER_FILENAME


def resolve_menu_query_model_path() -> Path:
    return _project_root() / "models" / _MENU_QUERY_MODEL_DIR


def clean_menu_search_text(value: object) -> str:
    return re.sub(r"\s+", " ", str(value or "").replace("\u200b", " ")).strip()


def build_menu_search_text(menu_name: object, menu_description: object | None = None) -> str:
    return clean_menu_search_text(
        " ".join(
            part
            for part in [
                clean_menu_search_text(menu_name),
                clean_menu_search_text(menu_description),
            ]
            if part
        )
    )


def build_menu_vector_text(
    menu_name: object,
    menu_description: object | None = None,
    *,
    vibe_labels: list[str] | None = None,
) -> str:
    parts = [build_menu_search_text(menu_name, menu_description)]
    normalized_vibe_labels = [clean_menu_search_text(label) for label in (vibe_labels or []) if label]
    if normalized_vibe_labels:
        parts.append(f"[\uacf5\uac04 \ud2b9\uc9d5: {', '.join(normalized_vibe_labels)}]")
    return clean_menu_search_text(" ".join(part for part in parts if part))


def _pad_vector(vector: np.ndarray, target_dim: int) -> list[float]:
    flat = np.asarray(vector, dtype=np.float32).reshape(-1)
    if flat.shape[0] > target_dim:
        return [float(value) for value in flat[:target_dim]]
    if flat.shape[0] < target_dim:
        padded = np.zeros(target_dim, dtype=np.float32)
        padded[: flat.shape[0]] = flat
        flat = padded
    return [float(value) for value in flat]


def _import_menu_query_libraries() -> tuple[Any, Any, Any]:
    try:
        import torch
    except ImportError as exc:
        raise RuntimeError("PyTorch is required to encode menu queries.") from exc

    try:
        from transformers import AutoModel, AutoTokenizer
    except ImportError as exc:
        raise RuntimeError("transformers is required to encode menu queries.") from exc

    return AutoModel, AutoTokenizer, torch


def _load_local_menu_query_components(
    model_path: Path,
    AutoModel: Any,
    AutoTokenizer: Any,
) -> tuple[Any, Any]:
    tokenizer = AutoTokenizer.from_pretrained(
        str(model_path),
        local_files_only=True,
    )
    model = AutoModel.from_pretrained(
        str(model_path),
        local_files_only=True,
    )
    return tokenizer, model


def _download_menu_query_components(
    model_path: Path,
    hf_token: str | None,
    AutoModel: Any,
    AutoTokenizer: Any,
) -> None:
    model_path.mkdir(parents=True, exist_ok=True)

    try:
        tokenizer = AutoTokenizer.from_pretrained(
            _MENU_QUERY_MODEL_NAME,
            token=hf_token,
        )
        model = AutoModel.from_pretrained(
            _MENU_QUERY_MODEL_NAME,
            token=hf_token,
        )
    except Exception as exc:
        raise RuntimeError(
            f"Failed to download menu query components from '{_MENU_QUERY_MODEL_NAME}': {exc}"
        ) from exc

    tokenizer.save_pretrained(str(model_path))
    model.save_pretrained(str(model_path))


@lru_cache(maxsize=1)
def _load_menu_query_components() -> tuple[Any, Any, Any]:
    model_path = resolve_menu_query_model_path()
    AutoModel, AutoTokenizer, torch = _import_menu_query_libraries()
    hf_token = os.getenv("HF_TOKEN")

    try:
        tokenizer, model = _load_local_menu_query_components(
            model_path,
            AutoModel,
            AutoTokenizer,
        )
    except Exception:
        _download_menu_query_components(
            model_path,
            hf_token,
            AutoModel,
            AutoTokenizer,
        )
        try:
            tokenizer, model = _load_local_menu_query_components(
                model_path,
                AutoModel,
                AutoTokenizer,
            )
        except Exception as exc:
            raise RuntimeError(
                f"Failed to load menu query components from '{model_path}': {exc}"
            ) from exc

    if hasattr(model, "to"):
        model.to("cpu")
    model.eval()
    logger.info(
        "menu_query_model_loaded: model_path=%s model_name=%s",
        model_path,
        _MENU_QUERY_MODEL_NAME,
    )
    return tokenizer, model, torch


def _mean_pool(last_hidden_state: Any, attention_mask: Any, torch: Any) -> Any:
    expanded_mask = attention_mask.unsqueeze(-1).expand(last_hidden_state.size()).float()
    masked_hidden_state = last_hidden_state * expanded_mask
    summed_hidden_state = masked_hidden_state.sum(dim=1)
    token_counts = expanded_mask.sum(dim=1).clamp(min=1e-9)
    return summed_hidden_state / token_counts


def _encode_menu_texts(texts: list[str], *, batch_size: int = _MENU_QUERY_BATCH_SIZE) -> np.ndarray:
    normalized_texts = [clean_menu_search_text(text) for text in texts if clean_menu_search_text(text)]
    if not normalized_texts:
        return np.zeros((0, _MENU_QUERY_VECTOR_DIMENSIONS), dtype=np.float32)

    tokenizer, model, torch = _load_menu_query_components()
    embeddings: list[np.ndarray] = []

    for batch_start in range(0, len(normalized_texts), batch_size):
        batch_texts = normalized_texts[batch_start : batch_start + batch_size]
        encoded_inputs = tokenizer(
            batch_texts,
            return_tensors="pt",
            padding=True,
            truncation=True,
            max_length=256,
        )
        with torch.no_grad():
            outputs = model(**encoded_inputs)
        pooled_output = _mean_pool(outputs.last_hidden_state, encoded_inputs["attention_mask"], torch)
        normalized_output = torch.nn.functional.normalize(pooled_output, p=2, dim=1)
        embeddings.append(normalized_output.cpu().numpy().astype(np.float32))

    return np.vstack(embeddings)


def _fit_projection(embeddings: np.ndarray, *, target_dim: int = _MENU_QUERY_VECTOR_DIMENSIONS) -> Any:
    if embeddings.ndim != 2 or embeddings.shape[0] == 0:
        raise ValueError("Projection requires at least one embedding row.")
    component_count = min(target_dim, embeddings.shape[0], embeddings.shape[1])
    return TruncatedSVD(n_components=component_count, random_state=42).fit(embeddings)


def _project_embeddings(embeddings: np.ndarray, projection: Any, *, target_dim: int) -> np.ndarray:
    projected_embeddings = projection.transform(embeddings)
    normalized_embeddings = normalize(projected_embeddings.astype(np.float32))
    padded_vectors = np.zeros((normalized_embeddings.shape[0], target_dim), dtype=np.float32)
    padded_vectors[:, : normalized_embeddings.shape[1]] = normalized_embeddings
    return padded_vectors


def _save_menu_query_encoder(
    projection: Any,
    artifact_path: Path,
    *,
    target_dim: int = _MENU_QUERY_VECTOR_DIMENSIONS,
) -> Path:
    artifact_path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "projection": projection,
        "target_dim": int(target_dim),
        "model_name": _MENU_QUERY_MODEL_NAME,
        "search_text_source": _MENU_SEARCH_TEXT_SOURCE,
        "vector_text_source": _MENU_VECTOR_TEXT_SOURCE,
    }
    with artifact_path.open("wb") as file:
        pickle.dump(payload, file)
    return artifact_path


@lru_cache(maxsize=1)
def load_menu_query_encoder() -> MenuQueryEncoderArtifact:
    artifact_path = resolve_menu_query_encoder_path()
    if not artifact_path.exists():
        raise RuntimeError(f"Menu query encoder artifact not found at '{artifact_path}'.")

    try:
        with artifact_path.open("rb") as file:
            payload = pickle.load(file)
    except Exception as exc:
        raise RuntimeError(
            f"Failed to load menu query encoder artifact from '{artifact_path}': {exc}"
        ) from exc

    projection = payload.get("projection")
    if projection is None or not hasattr(projection, "transform"):
        raise RuntimeError(f"Invalid menu query encoder artifact at '{artifact_path}'.")

    target_dim = int(payload.get("target_dim", _MENU_QUERY_VECTOR_DIMENSIONS))
    model_name = str(payload.get("model_name", _MENU_QUERY_MODEL_NAME))
    search_text_source = str(payload.get("search_text_source", _MENU_SEARCH_TEXT_SOURCE))
    vector_text_source = str(payload.get("vector_text_source", _MENU_VECTOR_TEXT_SOURCE))
    logger.info(
        "menu_encoder_loaded: artifact_path=%s output_dim=%s model_name=%s search_text_source=%s vector_text_source=%s",
        artifact_path,
        target_dim,
        model_name,
        search_text_source,
        vector_text_source,
    )
    return MenuQueryEncoderArtifact(
        projection=projection,
        artifact_path=artifact_path,
        target_dim=target_dim,
        model_name=model_name,
        search_text_source=search_text_source,
        vector_text_source=vector_text_source,
    )


def encode_menu_query(text: str) -> list[float]:
    normalized_text = clean_menu_search_text(text)
    if not normalized_text:
        return []

    artifact = load_menu_query_encoder()
    raw_embeddings = _encode_menu_texts([normalized_text])
    if raw_embeddings.size == 0:
        return []
    projected_embeddings = _project_embeddings(
        raw_embeddings,
        artifact.projection,
        target_dim=artifact.target_dim,
    )
    return _pad_vector(projected_embeddings[0], artifact.target_dim)


def build_menu_encoder_and_records(
    rows: list[dict[str, Any]],
    *,
    artifact_path: Path | None = None,
) -> tuple[Path, list[dict[str, object]]]:
    if not rows:
        raise ValueError("At least one menu row is required to build menu search artifacts.")

    search_texts = [
        build_menu_search_text(row.get("menu_name"), row.get("menu_description"))
        for row in rows
    ]
    vector_texts = [
        build_menu_vector_text(
            row.get("menu_name"),
            row.get("menu_description"),
            vibe_labels=resolve_vibe_labels(list(row.get("vibe_tag_ids") or [])),
        )
        for row in rows
    ]
    raw_embeddings = _encode_menu_texts(vector_texts)
    projection = _fit_projection(raw_embeddings, target_dim=_MENU_QUERY_VECTOR_DIMENSIONS)
    projected_embeddings = _project_embeddings(
        raw_embeddings,
        projection,
        target_dim=_MENU_QUERY_VECTOR_DIMENSIONS,
    )

    resolved_artifact_path = artifact_path or resolve_menu_query_encoder_path()
    _save_menu_query_encoder(
        projection,
        resolved_artifact_path,
        target_dim=_MENU_QUERY_VECTOR_DIMENSIONS,
    )
    load_menu_query_encoder.cache_clear()

    records: list[dict[str, object]] = []
    for row, search_text, vector_text, vector in zip(
        rows,
        search_texts,
        vector_texts,
        projected_embeddings,
        strict=False,
    ):
        records.append(
            {
                "cafe_id": str(row.get("cafe_id") or ""),
                "menu_id": int(row["menu_id"]),
                "menu_name": clean_menu_search_text(row.get("menu_name")),
                "menu_description": clean_menu_search_text(row.get("menu_description")) or None,
                "menu_search_text": search_text,
                "menu_vector_source_text": vector_text,
                "menu_vector": _pad_vector(vector, _MENU_QUERY_VECTOR_DIMENSIONS),
            }
        )

    return resolved_artifact_path, records
