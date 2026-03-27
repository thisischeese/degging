from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from uuid import UUID

import torch
from torch import nn


PAD_MENU = "__PAD_MENU__"
MENU_SLOT_COUNT = 3
CAFE_SLOT_COUNT = 3
MOOD_VOCAB = [
    "우드톤/따뜻함",
    "식물원/플랜테리어",
    "힙한",
    "조용한/차분한",
    "탁트인/뷰 좋은",
]
MOOD_ALIAS_MAP = {
    "우드톤/따뜻한": "우드톤/따뜻함",
}


def _project_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _clean_whitespace(value: str) -> str:
    return re.sub(r"\s+", " ", value.replace("\u200b", " ")).strip()


def _normalize_menu_token(value: str) -> str:
    cleaned = _clean_whitespace(value)
    cleaned = re.sub(r"[\"'`]", "", cleaned)
    cleaned = re.sub(r"[()]+", " ", cleaned)
    cleaned = re.sub(r"[|]+", " ", cleaned)
    return _clean_whitespace(cleaned)


def _stable_bucket(value: str, bucket_size: int) -> int:
    digest = hashlib.sha256(value.encode("utf-8")).hexdigest()
    return int(digest[:16], 16) % bucket_size


def _masked_mean(embeddings: torch.Tensor, mask: torch.Tensor) -> torch.Tensor:
    weights = mask.unsqueeze(-1).float()
    total = (embeddings * weights).sum(dim=1)
    counts = weights.sum(dim=1).clamp_min(1.0)
    return total / counts


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
        input_dim = menu_embedding_dim + len(MOOD_VOCAB) + 8 + 8 + 4 + id_embedding_dim
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


@dataclass(slots=True)
class OnboardingInferenceArtifacts:
    menu_vocab: list[str]
    cafe_ids: list[str]
    bucket_size: int
    menu_embedding_dim: int
    id_embedding_dim: int
    hidden_dim: int
    embedding_dim: int
    dropout: float


class OnboardingInferenceEngine:
    def __init__(self) -> None:
        models_dir = _project_root() / "models"
        checkpoint_path = models_dir / "two_tower_model.pt"
        feature_bundle_path = models_dir / "feature_bundle.pt"

        checkpoint = torch.load(checkpoint_path, map_location="cpu", weights_only=False)
        feature_bundle = torch.load(feature_bundle_path, map_location="cpu", weights_only=False)
        training_config = checkpoint["training_config"]

        self.artifacts = OnboardingInferenceArtifacts(
            menu_vocab=list(feature_bundle["menu_vocab"]),
            cafe_ids=list(feature_bundle["cafe_ids"]),
            bucket_size=int(training_config["hash_bucket_size"]),
            menu_embedding_dim=int(training_config["menu_embedding_dim"]),
            id_embedding_dim=int(training_config["id_embedding_dim"]),
            hidden_dim=int(training_config["hidden_dim"]),
            embedding_dim=int(training_config["embedding_dim"]),
            dropout=float(training_config["dropout"]),
        )
        self.menu_vocab = self.artifacts.menu_vocab
        self.cafe_ids = self.artifacts.cafe_ids
        self.menu_to_index = {menu: index for index, menu in enumerate(self.menu_vocab)}
        self.cafe_to_index = {
            cafe_id: index + 1
            for index, cafe_id in enumerate(self.cafe_ids)
        }
        self.model = UserTower(
            menu_vocab_size=len(self.menu_vocab),
            cafe_vocab_size=len(self.cafe_ids) + 1,
            hash_bucket_size=self.artifacts.bucket_size,
            menu_embedding_dim=self.artifacts.menu_embedding_dim,
            id_embedding_dim=self.artifacts.id_embedding_dim,
            hidden_dim=self.artifacts.hidden_dim,
            output_dim=self.artifacts.embedding_dim,
            dropout=self.artifacts.dropout,
        )
        user_tower_state = {
            key.removeprefix("user_tower."): value
            for key, value in checkpoint["model_state_dict"].items()
            if key.startswith("user_tower.")
        }
        self.model.load_state_dict(user_tower_state)
        self.model.eval()

    def normalize_favorite_menus(self, favorite_menus: list[str]) -> list[str]:
        normalized: list[str] = []
        for value in favorite_menus:
            token = _normalize_menu_token(value)
            if token and token not in normalized:
                normalized.append(token)
            if len(normalized) == MENU_SLOT_COUNT:
                break
        while len(normalized) < MENU_SLOT_COUNT:
            normalized.append(PAD_MENU)
        return normalized

    def resolve_mood_tokens(self, mood_tags: list[str]) -> list[str]:
        matches: list[str] = []
        for value in mood_tags:
            piece = _clean_whitespace(value)
            if not piece:
                continue
            candidates = [MOOD_ALIAS_MAP.get(piece, piece), piece]
            for candidate in candidates:
                for mood in MOOD_VOCAB:
                    if mood in candidate and mood not in matches:
                        matches.append(mood)
                        break
                if len(matches) == MENU_SLOT_COUNT:
                    return matches
        return matches

    def build_mood_multihot(self, mood_tags: list[str]) -> list[float]:
        resolved = self.resolve_mood_tokens(mood_tags)
        return [1.0 if mood in resolved else 0.0 for mood in MOOD_VOCAB]

    def encode_cafes(self, cafes: list[UUID | str]) -> list[int]:
        encoded = [
            self.cafe_to_index.get(str(cafe_id), 0)
            for cafe_id in cafes[:CAFE_SLOT_COUNT]
        ]
        while len(encoded) < CAFE_SLOT_COUNT:
            encoded.append(0)
        return encoded

    def build_model_inputs(
        self,
        *,
        nickname: str,
        email: str,
        favorite_menus: list[str],
        mood_tags: list[str],
        cafes: list[UUID | str],
    ) -> dict[str, torch.Tensor]:
        normalized_nickname = _clean_whitespace(nickname)
        normalized_email = _clean_whitespace(email).lower()
        normalized_menus = self.normalize_favorite_menus(favorite_menus)
        mood_multihot = self.build_mood_multihot(mood_tags)
        preferred_cafe_ids = self.encode_cafes(cafes)
        domain = normalized_email.split("@", maxsplit=1)[-1]

        return {
            "menu_ids": torch.tensor(
                [[self.menu_to_index.get(menu, 0) for menu in normalized_menus]],
                dtype=torch.long,
            ),
            "mood_multihot": torch.tensor([mood_multihot], dtype=torch.float32),
            "nickname_bucket_ids": torch.tensor(
                [_stable_bucket(normalized_nickname, self.artifacts.bucket_size)],
                dtype=torch.long,
            ),
            "email_bucket_ids": torch.tensor(
                [_stable_bucket(normalized_email, self.artifacts.bucket_size)],
                dtype=torch.long,
            ),
            "domain_bucket_ids": torch.tensor(
                [_stable_bucket(domain, self.artifacts.bucket_size)],
                dtype=torch.long,
            ),
            "preferred_cafe_ids": torch.tensor([preferred_cafe_ids], dtype=torch.long),
        }

    def vectorize_user(
        self,
        *,
        nickname: str,
        email: str,
        favorite_menus: list[str],
        mood_tags: list[str],
        cafes: list[UUID | str],
    ) -> list[float]:
        model_inputs = self.build_model_inputs(
            nickname=nickname,
            email=email,
            favorite_menus=favorite_menus,
            mood_tags=mood_tags,
            cafes=cafes,
        )
        with torch.inference_mode():
            vector = self.model(**model_inputs)[0]
        return [float(value) for value in vector.tolist()]


@lru_cache(maxsize=1)
def get_onboarding_inference_engine() -> OnboardingInferenceEngine:
    return OnboardingInferenceEngine()
