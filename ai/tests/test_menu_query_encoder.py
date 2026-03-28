from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import numpy as np

from app.services.menu_query_encoder import (
    build_menu_encoder_and_records,
    build_menu_search_text,
    build_menu_vector_text,
    load_menu_query_encoder,
)


class MenuQueryEncoderTest(unittest.TestCase):
    def tearDown(self) -> None:
        load_menu_query_encoder.cache_clear()

    def test_build_menu_search_text_uses_name_and_description_only(self) -> None:
        self.assertEqual(
            build_menu_search_text("Salt Bread", "Buttery baked bread"),
            "Salt Bread Buttery baked bread",
        )

    def test_build_menu_vector_text_appends_vibe_labels(self) -> None:
        self.assertEqual(
            build_menu_vector_text(
                "Salt Bread",
                "Buttery baked bread",
                vibe_labels=["\uc870\uc6a9\ud55c/\ucc28\ubd84\ud55c", "\uc6b0\ub4dc\ud1a4/\ub530\ub73b\ud568"],
            ),
            "Salt Bread Buttery baked bread [\uacf5\uac04 \ud2b9\uc9d5: \uc870\uc6a9\ud55c/\ucc28\ubd84\ud55c, \uc6b0\ub4dc\ud1a4/\ub530\ub73b\ud568]",
        )

    def test_build_menu_encoder_and_records_uses_vibe_labels_for_dense_document(self) -> None:
        rows = [
            {
                "cafe_id": "123e4567-e89b-12d3-a456-426614174001",
                "menu_id": 1,
                "menu_name": "Salt Bread",
                "menu_description": "Buttery baked bread",
                "vibe_tag_ids": ["e747e844-db71-42ea-81cf-c25d510672b2"],
            },
            {
                "cafe_id": "123e4567-e89b-12d3-a456-426614174002",
                "menu_id": 2,
                "menu_name": "Latte",
                "menu_description": "Smooth milk foam",
                "vibe_tag_ids": ["9b71769c-2293-4e06-bf37-f1fbf33c2853"],
            },
        ]
        with tempfile.TemporaryDirectory() as temp_dir:
            artifact_path = Path(temp_dir) / "test_menu_query_encoder.pkl"
            with patch(
                "app.services.menu_query_encoder._encode_menu_texts",
                return_value=np.asarray(
                    [
                        [1.0, 0.0, 0.0],
                        [0.0, 1.0, 0.0],
                    ],
                    dtype=np.float32,
                ),
            ):
                resolved_artifact_path, records = build_menu_encoder_and_records(
                    rows,
                    artifact_path=artifact_path,
                )

                self.assertEqual(resolved_artifact_path, artifact_path)
                self.assertTrue(artifact_path.exists())
                self.assertEqual(records[0]["menu_search_text"], "Salt Bread Buttery baked bread")
                self.assertEqual(
                    records[0]["menu_vector_source_text"],
                    "Salt Bread Buttery baked bread [\uacf5\uac04 \ud2b9\uc9d5: \uc870\uc6a9\ud55c/\ucc28\ubd84\ud55c]",
                )
                self.assertEqual(len(records[0]["menu_vector"]), 64)
