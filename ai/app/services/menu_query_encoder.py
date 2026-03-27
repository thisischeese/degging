from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
import logging
import pickle
from pathlib import Path
import re
from typing import TYPE_CHECKING, Any

import numpy as np

if TYPE_CHECKING:
    from twotower.text import AutoTextEncoder

logger = logging.getLogger("uvicorn.error")

_MENU_QUERY_ENCODER_FILENAME = "menu_query_encoder.pkl"
_MENU_QUERY_VECTOR_DIMENSIONS = 64
_MENU_TEXT_SOURCE = "menu_name+menu_description"


@dataclass(slots=True)
class MenuQueryEncoderArtifact:
    encoder: Any
    artifact_path: Path
    target_dim: int = _MENU_QUERY_VECTOR_DIMENSIONS
    text_source: str = _MENU_TEXT_SOURCE


def _project_root() -> Path:
    return Path(__file__).resolve().parents[2]


def resolve_menu_query_encoder_path() -> Path:
    return _project_root() / "models" / _MENU_QUERY_ENCODER_FILENAME


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


def _pad_vector(vector: np.ndarray, target_dim: int) -> list[float]:
    flat = np.asarray(vector, dtype=np.float32).reshape(-1)
    if flat.shape[0] > target_dim:
        return [float(value) for value in flat[:target_dim]]
    if flat.shape[0] < target_dim:
        padded = np.zeros(target_dim, dtype=np.float32)
        padded[: flat.shape[0]] = flat
        flat = padded
    return [float(value) for value in flat]


def _import_auto_text_encoder() -> type["AutoTextEncoder"]:
    try:
        from twotower.text import AutoTextEncoder as ImportedAutoTextEncoder
    except ImportError as exc:
        raise RuntimeError(
            "scikit-learn is required to build or load the menu query encoder artifact."
        ) from exc
    return ImportedAutoTextEncoder


def _save_menu_query_encoder(
    encoder: Any,
    artifact_path: Path,
    *,
    target_dim: int = _MENU_QUERY_VECTOR_DIMENSIONS,
) -> Path:
    artifact_path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "encoder": encoder,
        "target_dim": int(target_dim),
        "text_source": _MENU_TEXT_SOURCE,
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

    encoder = payload.get("encoder")
    auto_text_encoder = _import_auto_text_encoder()
    if not isinstance(encoder, auto_text_encoder):
        raise RuntimeError(f"Invalid menu query encoder artifact at '{artifact_path}'.")

    target_dim = int(payload.get("target_dim", _MENU_QUERY_VECTOR_DIMENSIONS))
    text_source = str(payload.get("text_source", _MENU_TEXT_SOURCE))
    logger.info(
        "menu_encoder_loaded: artifact_path=%s output_dim=%s text_source=%s",
        artifact_path,
        target_dim,
        text_source,
    )
    return MenuQueryEncoderArtifact(
        encoder=encoder,
        artifact_path=artifact_path,
        target_dim=target_dim,
        text_source=text_source,
    )


def encode_menu_query(text: str) -> list[float]:
    normalized_text = clean_menu_search_text(text)
    if not normalized_text:
        return []

    artifact = load_menu_query_encoder()
    encoded = artifact.encoder.transform([normalized_text])
    return _pad_vector(encoded[0], artifact.target_dim)


def build_menu_encoder_and_records(
    rows: list[dict[str, Any]],
    *,
    artifact_path: Path | None = None,
) -> tuple[Path, list[dict[str, object]]]:
    if not rows:
        raise ValueError("At least one menu row is required to build menu search artifacts.")

    texts = [
        build_menu_search_text(row.get("menu_name"), row.get("menu_description"))
        for row in rows
    ]
    auto_text_encoder = _import_auto_text_encoder()
    encoder = auto_text_encoder(
        backend="tfidf",
        tfidf_max_features=4096,
        svd_components=_MENU_QUERY_VECTOR_DIMENSIONS,
    )
    encoder.fit(texts)
    vectors = encoder.transform(texts)

    resolved_artifact_path = artifact_path or resolve_menu_query_encoder_path()
    _save_menu_query_encoder(
        encoder,
        resolved_artifact_path,
        target_dim=_MENU_QUERY_VECTOR_DIMENSIONS,
    )
    load_menu_query_encoder.cache_clear()

    records: list[dict[str, object]] = []
    for row, vector, text in zip(rows, vectors, texts):
        records.append(
            {
                "cafe_id": str(row.get("cafe_id") or ""),
                "menu_id": int(row["menu_id"]),
                "menu_name": clean_menu_search_text(row.get("menu_name")),
                "menu_description": clean_menu_search_text(row.get("menu_description")) or None,
                "menu_search_text": text,
                "menu_vector": _pad_vector(vector, _MENU_QUERY_VECTOR_DIMENSIONS),
            }
        )

    return resolved_artifact_path, records
