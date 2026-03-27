from contextlib import nullcontext
from pathlib import Path
import unittest
from unittest.mock import AsyncMock, patch
from uuid import UUID

from app.services.query_preprocess_service import (
    QueryPreprocessService,
    _load_menu_ner_components,
    _resolve_food_label_ids,
)


class FakeLogits:
    def __init__(self, predicted_ids: list[int]) -> None:
        self._predicted_ids = predicted_ids

    def argmax(self, dim: int = -1) -> list[list[int]]:
        if dim != -1:
            raise AssertionError(f"Unexpected argmax dim: {dim}")
        return [self._predicted_ids]


class FakeOutputs:
    def __init__(self, predicted_ids: list[int]) -> None:
        self.logits = FakeLogits(predicted_ids)


class FakeModel:
    def __init__(self, predicted_ids: list[int], id2label: dict[int, str] | None = None) -> None:
        self._predicted_ids = predicted_ids
        self.config = type("Config", (), {"id2label": id2label or {}})()
        self.calls: list[dict[str, object]] = []

    def __call__(self, **kwargs: object) -> FakeOutputs:
        self.calls.append(kwargs)
        return FakeOutputs(self._predicted_ids)


class FakeTokenizer:
    def __init__(
        self,
        offset_mapping: list[list[tuple[int, int]]],
        special_tokens_mask: list[list[int]],
    ) -> None:
        self._offset_mapping = offset_mapping
        self._special_tokens_mask = special_tokens_mask
        self.calls: list[tuple[str, dict[str, object]]] = []

    def __call__(self, text: str, **kwargs: object) -> dict[str, object]:
        self.calls.append((text, kwargs))
        sequence_length = len(self._special_tokens_mask[0])
        return {
            "input_ids": [[0] * sequence_length],
            "attention_mask": [[1] * sequence_length],
            "token_type_ids": [[0] * sequence_length],
            "offset_mapping": self._offset_mapping,
            "special_tokens_mask": self._special_tokens_mask,
        }


class FakeTorch:
    @staticmethod
    def no_grad():
        return nullcontext()


class LoadableTokenizer:
    def __init__(self, source: str) -> None:
        self.source = source


class LoadableModel:
    def __init__(self, source: str) -> None:
        self.source = source
        self.config = type("Config", (), {"id2label": {0: "O", 1: "LABEL_27"}})()
        self.to_calls: list[str] = []
        self.eval_called = False

    def to(self, device: str) -> None:
        self.to_calls.append(device)

    def eval(self) -> None:
        self.eval_called = True


class QueryPreprocessServiceTest(unittest.IsolatedAsyncioTestCase):
    async def test_encode_query_returns_empty_when_menu_encoder_is_unavailable(self) -> None:
        service = QueryPreprocessService()

        with patch(
            "app.services.query_preprocess_service.encode_menu_query",
            side_effect=RuntimeError("missing artifact"),
        ):
            vector = await service.encode_query("americano")

        self.assertEqual(vector, [])

    async def test_extract_menu_phrases_uses_ner_and_mecab_together(self) -> None:
        service = QueryPreprocessService()
        tokenizer = FakeTokenizer(
            offset_mapping=[[(0, 0), (0, 4), (0, 0)]],
            special_tokens_mask=[[1, 0, 1]],
        )
        model = FakeModel(predicted_ids=[299, 27, 299])
        mecab_rows = [
            {"alias": "word", "token": "latte", "lexemes": ["latte"]},
            {"alias": "word", "token": "coffee", "lexemes": ["coffee"]},
            {"alias": "word", "token": "want", "lexemes": ["want"]},
        ]

        with (
            patch.object(service, "log_mecab_analysis", AsyncMock(return_value=mecab_rows)),
            patch(
                "app.services.query_preprocess_service._load_menu_ner_components",
                return_value=(tokenizer, model, FakeTorch()),
            ),
        ):
            phrases = await service.extract_menu_phrases("latte coffee")

        self.assertEqual(phrases, ["latte", "coffee"])

    async def test_extract_menu_phrases_returns_empty_for_blank_query_without_loading_model(
        self,
    ) -> None:
        service = QueryPreprocessService()

        with patch(
            "app.services.query_preprocess_service._load_menu_ner_components",
        ) as load_components:
            phrases = await service.extract_menu_phrases("   ")

        self.assertEqual(phrases, [])
        load_components.assert_not_called()

    async def test_preprocess_does_not_use_query_fallback_and_logs_completion(self) -> None:
        service = QueryPreprocessService()

        with (
            patch.object(service, "extract_menu_phrases", AsyncMock(return_value=[])),
            patch.object(service, "encode_query", AsyncMock(return_value=[0.1, 0.2])) as encode_query,
            self.assertLogs("uvicorn.error", level="INFO") as logs,
        ):
            processed = await service.preprocess("americano")

        self.assertEqual(processed.menu_phrases, [])
        self.assertEqual(processed.phrase_vectors, {})
        self.assertEqual(processed.vector, [])
        self.assertFalse(processed.used_query_fallback)
        encode_query.assert_not_called()
        self.assertTrue(
            any(
                "menu_phrase_extraction_completed" in message
                and "used_query_fallback=False" in message
                for message in logs.output
            )
        )

    async def test_preprocess_query_encodes_first_menu_phrase_for_public_payload(self) -> None:
        service = QueryPreprocessService()

        with (
            patch.object(service, "extract_menu_phrases", AsyncMock(return_value=["latte"])),
            patch.object(service, "encode_query", AsyncMock(return_value=[0.1, 0.2])),
        ):
            payload = await service.preprocess_query(
                "latte",
                user_id=UUID("123e4567-e89b-12d3-a456-426614174000"),
            )

        self.assertEqual(payload.original_query, "latte")
        self.assertEqual(payload.vector, [0.1, 0.2])
        self.assertEqual(payload.dimensions, 2)
        self.assertEqual(payload.extracted_menus, {})


class QueryPreprocessServiceLoaderTest(unittest.TestCase):
    def tearDown(self) -> None:
        _load_menu_ner_components.cache_clear()

    def test_resolve_food_label_ids_falls_back_for_generic_labels(self) -> None:
        model = FakeModel(
            predicted_ids=[0],
            id2label={0: "O", 27: "LABEL_27", 28: "LABEL_28", 178: "LABEL_178"},
        )
        label_ids, label_source = _resolve_food_label_ids(model)
        self.assertEqual(label_ids, frozenset({27, 28, 178}))
        self.assertEqual(label_source, "fallback")

    def test_load_menu_ner_components_downloads_into_food_model_dir_when_missing(self) -> None:
        model_path = Path("C:/tmp/food_ner_model")
        tokenizer = LoadableTokenizer(str(model_path))
        model = LoadableModel(str(model_path))
        fake_auto_tokenizer = object()
        fake_bert_model = object()
        fake_torch = FakeTorch()
        _load_menu_ner_components.cache_clear()

        with (
            patch(
                "app.services.query_preprocess_service._resolve_menu_ner_model_path",
                return_value=model_path,
            ),
            patch(
                "app.services.query_preprocess_service._import_menu_ner_libraries",
                return_value=(fake_auto_tokenizer, fake_bert_model, fake_torch),
            ),
            patch(
                "app.services.query_preprocess_service._load_local_menu_ner_components",
                side_effect=[
                    OSError("missing local files"),
                    (tokenizer, model),
                ],
            ) as load_local,
            patch(
                "app.services.query_preprocess_service._download_menu_ner_components",
            ) as download_components,
            patch(
                "app.services.query_preprocess_service.os.getenv",
                return_value="hf-test-token",
            ),
            self.assertLogs("uvicorn.error", level="INFO") as logs,
        ):
            loaded_tokenizer, loaded_model, torch = _load_menu_ner_components()

        self.assertIs(loaded_tokenizer, tokenizer)
        self.assertIs(loaded_model, model)
        self.assertIs(torch, fake_torch)
        self.assertEqual(load_local.call_count, 2)
        download_components.assert_called_once_with(
            model_path,
            "hf-test-token",
            fake_auto_tokenizer,
            fake_bert_model,
        )
        self.assertEqual(model.to_calls, ["cpu"])
        self.assertTrue(model.eval_called)
        self.assertTrue(any("menu_ner_components_loaded" in message for message in logs.output))
