import json
import unittest
from pathlib import Path
from uuid import UUID

import torch

from app.services.onboarding_inference import MOOD_VOCAB, OnboardingInferenceEngine


class OnboardingInferenceTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.engine = OnboardingInferenceEngine()
        root = Path(__file__).resolve().parents[1]
        cls.feature_bundle = torch.load(
            root / "models" / "feature_bundle.pt",
            map_location="cpu",
            weights_only=False,
        )
        cls.user_vectors = json.loads((root / "user_vectors.json").read_text(encoding="utf-8"))

    def _request_like_payload(self, row_index: int) -> dict[str, object]:
        record = self.user_vectors[row_index]
        menu_ids = self.feature_bundle["user_menu_ids"][row_index].tolist()
        mood_vector = self.feature_bundle["user_mood_multihot"][row_index].tolist()
        preferred_cafe_indices = self.feature_bundle["user_preferred_cafe_indices"][row_index].tolist()

        return {
            "nickname": record["nickname"],
            "email": record["email"],
            "favorite_menus": [
                self.feature_bundle["menu_vocab"][index]
                for index in menu_ids
                if index != 0
            ],
            "mood_tags": [
                mood
                for mood, enabled in zip(MOOD_VOCAB, mood_vector, strict=False)
                if enabled > 0.0
            ],
            "cafes": [
                self.feature_bundle["cafe_ids"][index - 1]
                for index in preferred_cafe_indices
                if index > 0
            ],
            "expected_vector": record["user_vector"],
        }

    def test_vectorize_user_matches_export_for_row_without_menu_padding(self) -> None:
        payload = self._request_like_payload(0)

        vector = self.engine.vectorize_user(
            nickname=payload["nickname"],
            email=payload["email"],
            favorite_menus=payload["favorite_menus"],
            mood_tags=payload["mood_tags"],
            cafes=payload["cafes"],
        )

        max_abs_diff = max(
            abs(actual - expected)
            for actual, expected in zip(vector, payload["expected_vector"], strict=False)
        )
        self.assertLess(max_abs_diff, 1e-6)

    def test_vectorize_user_matches_export_for_row_with_menu_padding(self) -> None:
        padded_row_index = next(
            index
            for index, menu_ids in enumerate(self.feature_bundle["user_menu_ids"])
            if 0 in menu_ids.tolist()
        )
        payload = self._request_like_payload(padded_row_index)

        vector = self.engine.vectorize_user(
            nickname=payload["nickname"],
            email=payload["email"],
            favorite_menus=payload["favorite_menus"],
            mood_tags=payload["mood_tags"],
            cafes=payload["cafes"],
        )

        max_abs_diff = max(
            abs(actual - expected)
            for actual, expected in zip(vector, payload["expected_vector"], strict=False)
        )
        self.assertLess(max_abs_diff, 1e-6)

    def test_build_model_inputs_normalizes_unknowns_and_aliases(self) -> None:
        known_cafe_id = UUID(self.feature_bundle["cafe_ids"][0])
        model_inputs = self.engine.build_model_inputs(
            nickname="  NewUser  ",
            email="  NewUser@Example.com  ",
            favorite_menus=["두쫀쿠", "두쫀쿠", "버터떡"],
            mood_tags=["우드톤/따뜻한", "빛나는?"],
            cafes=[known_cafe_id, UUID("00000000-0000-0000-0000-000000000000")],
        )

        self.assertEqual(model_inputs["menu_ids"].tolist(), [[1, 0, 0]])
        self.assertEqual(model_inputs["mood_multihot"].tolist(), [[1.0, 0.0, 0.0, 0.0, 0.0]])
        self.assertEqual(model_inputs["preferred_cafe_ids"].tolist(), [[1, 0, 0]])
