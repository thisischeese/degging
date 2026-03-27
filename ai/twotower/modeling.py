"""Feature construction and model definitions for the two-tower pipeline."""

from __future__ import annotations

from dataclasses import asdict, dataclass
import hashlib

import numpy as np
import pandas as pd
import torch
from torch import nn
from torch.utils.data import Dataset

from twotower.config import AppConfig
from twotower.constants import MOOD_TO_INDEX, PAD_MENU
from twotower.text import AutoTextEncoder


def _stable_bucket(value: str, bucket_size: int) -> int:
    digest = hashlib.sha256(value.encode("utf-8")).hexdigest()
    return int(digest[:16], 16) % bucket_size


def _masked_mean(embeddings: torch.Tensor, mask: torch.Tensor) -> torch.Tensor:
    weights = mask.unsqueeze(-1).float()
    total = (embeddings * weights).sum(dim=1)
    counts = weights.sum(dim=1).clamp_min(1.0)
    return total / counts


def _flatten_structured_features(cafe_df: pd.DataFrame) -> np.ndarray:
    rows: list[list[float]] = []
    for _, row in cafe_df.iterrows():
        menu_stats = row["menu_price_stats"]
        review_stats = row["review_rating_stats"]
        hour_stats = row["business_hour_features"]
        values = [
            np.log1p(float(menu_stats.get("menu_count", 0.0))),
            np.log1p(float(menu_stats.get("price_min", 0.0))),
            np.log1p(float(menu_stats.get("price_max", 0.0))),
            np.log1p(float(menu_stats.get("price_mean", 0.0))),
            np.log1p(float(review_stats.get("review_count", 0.0))),
            float(review_stats.get("review_rating_mean", 0.0)),
            float(review_stats.get("review_rating_std", 0.0)),
            float(hour_stats.get("open_days_count", 0.0)),
            np.log1p(float(hour_stats.get("weekday_open_minutes", 0.0))),
            np.log1p(float(hour_stats.get("weekend_open_minutes", 0.0))),
            float(hour_stats.get("opens_before_09", 0.0)),
            float(hour_stats.get("closes_after_21", 0.0)),
        ]
        for key in sorted(hour_stats):
            if key.endswith("_open"):
                values.append(float(hour_stats.get(key, 0.0)))
        values.append(1.0 if not row["cafe_intro"] else 0.0)
        values.append(1.0 if not row["review_text"] else 0.0)
        rows.append(values)
    return np.asarray(rows, dtype=np.float32)


@dataclass(slots=True)
class FeatureBundle:
    user_ids: list[str]
    cafe_ids: list[str]
    user_menu_ids: np.ndarray
    user_mood_multihot: np.ndarray
    user_nickname_buckets: np.ndarray
    user_email_buckets: np.ndarray
    user_domain_buckets: np.ndarray
    user_preferred_cafe_indices: np.ndarray
    positive_cafe_indices: np.ndarray
    cafe_text_features: np.ndarray
    cafe_struct_features: np.ndarray
    train_user_indices: np.ndarray
    val_user_indices: np.ndarray
    test_user_indices: np.ndarray
    menu_vocab: list[str]
    text_encoder_info: dict[str, dict[str, str | int]]

    def to_dict(self) -> dict[str, object]:
        return {
            "user_ids": self.user_ids,
            "cafe_ids": self.cafe_ids,
            "user_menu_ids": self.user_menu_ids,
            "user_mood_multihot": self.user_mood_multihot,
            "user_nickname_buckets": self.user_nickname_buckets,
            "user_email_buckets": self.user_email_buckets,
            "user_domain_buckets": self.user_domain_buckets,
            "user_preferred_cafe_indices": self.user_preferred_cafe_indices,
            "positive_cafe_indices": self.positive_cafe_indices,
            "cafe_text_features": self.cafe_text_features,
            "cafe_struct_features": self.cafe_struct_features,
            "train_user_indices": self.train_user_indices,
            "val_user_indices": self.val_user_indices,
            "test_user_indices": self.test_user_indices,
            "menu_vocab": self.menu_vocab,
            "text_encoder_info": self.text_encoder_info,
        }

    @classmethod
    def from_dict(cls, payload: dict[str, object]) -> "FeatureBundle":
        return cls(**payload)


def build_feature_bundle(
    *,
    user_df: pd.DataFrame,
    cafe_df: pd.DataFrame,
    split_df: pd.DataFrame,
    config: AppConfig,
) -> FeatureBundle:
    """Build model-ready tensors and metadata from prepared artifacts."""
    menu_vocab = [PAD_MENU]
    for menus in user_df["preferred_menus"]:
        for menu in menus:
            if menu != PAD_MENU and menu not in menu_vocab:
                menu_vocab.append(menu)
    menu_to_index = {menu: index for index, menu in enumerate(menu_vocab)}
    cafe_to_index = {cafe_id: index + 1 for index, cafe_id in enumerate(cafe_df["cafe_id"].tolist())}

    user_menu_ids = np.asarray(
        [[menu_to_index.get(menu, 0) for menu in menus] for menus in user_df["preferred_menus"]],
        dtype=np.int64,
    )

    mood_multihot = np.zeros((len(user_df), len(MOOD_TO_INDEX)), dtype=np.float32)
    for row_index, moods in enumerate(user_df["mood_tags"]):
        for mood in moods:
            mood_index = MOOD_TO_INDEX.get(mood)
            if mood_index is not None:
                mood_multihot[row_index, mood_index] = 1.0

    nickname_buckets = np.asarray(
        [_stable_bucket(value, config.training.hash_bucket_size) for value in user_df["nickname"]],
        dtype=np.int64,
    )
    email_buckets = np.asarray(
        [_stable_bucket(value, config.training.hash_bucket_size) for value in user_df["email"]],
        dtype=np.int64,
    )
    domain_buckets = np.asarray(
        [_stable_bucket(value.split("@", maxsplit=1)[-1], config.training.hash_bucket_size) for value in user_df["email"]],
        dtype=np.int64,
    )
    preferred_cafe_indices = np.asarray(
        [[cafe_to_index.get(cafe_id, 0) for cafe_id in cafe_ids] for cafe_ids in user_df["preferred_cafe_ids"]],
        dtype=np.int64,
    )

    name_intro_encoder = AutoTextEncoder(
        backend=config.text.backend,
        model_name=config.text.model_name,
        allow_model_download=config.text.allow_model_download,
        tfidf_max_features=config.text.tfidf_max_features,
        svd_components=config.text.svd_components,
        random_seed=config.training.random_seed,
        device="cuda" if config.training.device == "cuda" else "cpu",
    )
    menu_encoder = AutoTextEncoder(
        backend=config.text.backend,
        model_name=config.text.model_name,
        allow_model_download=config.text.allow_model_download,
        tfidf_max_features=config.text.tfidf_max_features,
        svd_components=config.text.svd_components,
        random_seed=config.training.random_seed,
        device="cuda" if config.training.device == "cuda" else "cpu",
    )
    review_encoder = AutoTextEncoder(
        backend=config.text.backend,
        model_name=config.text.model_name,
        allow_model_download=config.text.allow_model_download,
        tfidf_max_features=config.text.tfidf_max_features,
        svd_components=config.text.svd_components,
        random_seed=config.training.random_seed,
        device="cuda" if config.training.device == "cuda" else "cpu",
    )

    name_intro_texts = (cafe_df["name"].fillna("") + " " + cafe_df["cafe_intro"].fillna("")).tolist()
    menu_texts = cafe_df["menu_text"].fillna("").tolist()
    review_texts = cafe_df["review_text"].fillna("").tolist()

    name_intro_vectors = name_intro_encoder.fit_transform(name_intro_texts)
    menu_vectors = menu_encoder.fit_transform(menu_texts)
    review_vectors = review_encoder.fit_transform(review_texts)
    text_features = np.concatenate([name_intro_vectors, menu_vectors, review_vectors], axis=1).astype(np.float32)
    struct_features = _flatten_structured_features(cafe_df)

    splits = split_df.set_index("user_id")["split"].to_dict()
    train_user_indices = np.asarray(
        [index for index, user_id in enumerate(user_df["user_id"]) if splits[user_id] == "train"], dtype=np.int64
    )
    val_user_indices = np.asarray(
        [index for index, user_id in enumerate(user_df["user_id"]) if splits[user_id] == "val"], dtype=np.int64
    )
    test_user_indices = np.asarray(
        [index for index, user_id in enumerate(user_df["user_id"]) if splits[user_id] == "test"], dtype=np.int64
    )

    encoder_info = {
        "name_intro": asdict(name_intro_encoder.info),
        "menu": asdict(menu_encoder.info),
        "review": asdict(review_encoder.info),
    }

    return FeatureBundle(
        user_ids=user_df["user_id"].tolist(),
        cafe_ids=cafe_df["cafe_id"].tolist(),
        user_menu_ids=user_menu_ids,
        user_mood_multihot=mood_multihot,
        user_nickname_buckets=nickname_buckets,
        user_email_buckets=email_buckets,
        user_domain_buckets=domain_buckets,
        user_preferred_cafe_indices=preferred_cafe_indices,
        positive_cafe_indices=preferred_cafe_indices.copy(),
        cafe_text_features=text_features,
        cafe_struct_features=struct_features,
        train_user_indices=train_user_indices,
        val_user_indices=val_user_indices,
        test_user_indices=test_user_indices,
        menu_vocab=menu_vocab,
        text_encoder_info=encoder_info,
    )


class PositivePreferenceDataset(Dataset):
    """Expose one positive cafe per user for the current epoch."""

    def __init__(self, user_indices: np.ndarray, positive_cafe_indices: np.ndarray) -> None:
        self.user_indices = user_indices
        self.positive_cafe_indices = positive_cafe_indices
        self._epoch = 0

    def set_epoch(self, epoch: int) -> None:
        self._epoch = epoch

    def __len__(self) -> int:
        return len(self.user_indices)

    def __getitem__(self, index: int) -> tuple[torch.Tensor, torch.Tensor]:
        user_index = int(self.user_indices[index])
        cafe_index = int(self.positive_cafe_indices[user_index, self._epoch % 3])
        return torch.tensor(user_index, dtype=torch.long), torch.tensor(cafe_index - 1, dtype=torch.long)


def _build_mlp(input_dim: int, hidden_dim: int, output_dim: int, dropout: float) -> nn.Sequential:
    return nn.Sequential(
        nn.Linear(input_dim, hidden_dim),
        nn.GELU(),
        nn.Dropout(dropout),
        nn.Linear(hidden_dim, hidden_dim // 2),
        nn.GELU(),
        nn.Dropout(dropout),
        nn.Linear(hidden_dim // 2, output_dim),
    )


class UserTower(nn.Module):
    def __init__(
        self,
        *,
        menu_vocab_size: int,
        cafe_vocab_size: int,
        hash_bucket_size: int,
        menu_embedding_dim: int,
        id_embedding_dim: int,
        hidden_dim: int,
        output_dim: int,
        dropout: float,
    ) -> None:
        super().__init__()
        self.menu_embedding = nn.Embedding(menu_vocab_size, menu_embedding_dim, padding_idx=0)
        self.nickname_embedding = nn.Embedding(hash_bucket_size, 8)
        self.email_embedding = nn.Embedding(hash_bucket_size, 8)
        self.domain_embedding = nn.Embedding(hash_bucket_size, 4)
        self.cafe_id_embedding = nn.Embedding(cafe_vocab_size, id_embedding_dim, padding_idx=0)
        input_dim = menu_embedding_dim + len(MOOD_TO_INDEX) + 8 + 8 + 4 + id_embedding_dim
        self.network = _build_mlp(input_dim, hidden_dim, output_dim, dropout)

    def forward(
        self,
        *,
        menu_ids: torch.Tensor,
        mood_multihot: torch.Tensor,
        nickname_bucket_ids: torch.Tensor,
        email_bucket_ids: torch.Tensor,
        domain_bucket_ids: torch.Tensor,
        preferred_cafe_ids: torch.Tensor,
    ) -> torch.Tensor:
        menu_mask = menu_ids.ne(0)
        menu_embeddings = _masked_mean(self.menu_embedding(menu_ids), menu_mask)

        preferred_mask = preferred_cafe_ids.ne(0)
        preferred_embeddings = _masked_mean(self.cafe_id_embedding(preferred_cafe_ids), preferred_mask)

        concatenated = torch.cat(
            [
                menu_embeddings,
                mood_multihot,
                self.nickname_embedding(nickname_bucket_ids),
                self.email_embedding(email_bucket_ids),
                self.domain_embedding(domain_bucket_ids),
                preferred_embeddings,
            ],
            dim=1,
        )
        return torch.nn.functional.normalize(self.network(concatenated), dim=1)


class CafeTower(nn.Module):
    def __init__(self, *, input_dim: int, hidden_dim: int, output_dim: int, dropout: float) -> None:
        super().__init__()
        self.network = _build_mlp(input_dim, hidden_dim, output_dim, dropout)

    def forward(self, *, text_features: torch.Tensor, struct_features: torch.Tensor) -> torch.Tensor:
        concatenated = torch.cat([text_features, struct_features], dim=1)
        return torch.nn.functional.normalize(self.network(concatenated), dim=1)


class PositiveOnlyTwoTowerModel(nn.Module):
    def __init__(self, *, bundle: FeatureBundle, config: AppConfig) -> None:
        super().__init__()
        self.user_tower = UserTower(
            menu_vocab_size=len(bundle.menu_vocab),
            cafe_vocab_size=len(bundle.cafe_ids) + 1,
            hash_bucket_size=config.training.hash_bucket_size,
            menu_embedding_dim=config.training.menu_embedding_dim,
            id_embedding_dim=config.training.id_embedding_dim,
            hidden_dim=config.training.hidden_dim,
            output_dim=config.training.embedding_dim,
            dropout=config.training.dropout,
        )
        self.cafe_tower = CafeTower(
            input_dim=bundle.cafe_text_features.shape[1] + bundle.cafe_struct_features.shape[1],
            hidden_dim=config.training.hidden_dim,
            output_dim=config.training.embedding_dim,
            dropout=config.training.dropout,
        )

    def get_user_embeddings(self, batch: dict[str, torch.Tensor]) -> torch.Tensor:
        return self.user_tower(**batch)

    def get_cafe_embeddings(self, *, text_features: torch.Tensor, struct_features: torch.Tensor) -> torch.Tensor:
        return self.cafe_tower(text_features=text_features, struct_features=struct_features)

    def forward(
        self,
        *,
        user_batch: dict[str, torch.Tensor],
        cafe_text_features: torch.Tensor,
        cafe_struct_features: torch.Tensor,
    ) -> tuple[torch.Tensor, torch.Tensor]:
        return self.get_user_embeddings(user_batch), self.get_cafe_embeddings(
            text_features=cafe_text_features,
            struct_features=cafe_struct_features,
        )
