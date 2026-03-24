from contextlib import nullcontext
from pathlib import Path
import unittest
from unittest.mock import patch

from app.services.query_preprocess_service import (
    QueryPreprocessService,
    _load_menu_ner_components,
)


class FakeLogits:
    def __init__(self, predicted_ids: list[int], num_labels: int = 3) -> None:
        self._predicted_ids = predicted_ids
        self._num_labels = num_labels

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
    async def test_extract_menu_phrases_merges_adjacent_food_tokens(self) -> None:
        service = QueryPreprocessService()
        tokenizer = FakeTokenizer(
            offset_mapping=[[(0, 0), (0, 3), (4, 9), (10, 14), (0, 0)]],
            special_tokens_mask=[[1, 0, 0, 0, 1]],
        )
        model = FakeModel(
            predicted_ids=[299, 28, 178, 0, 299],
        )

        with patch(
            "app.services.query_preprocess_service._load_menu_ner_components",
            return_value=(tokenizer, model, FakeTorch()),
        ):
            phrases = await service.extract_menu_phrases("ice cream shop")

        self.assertEqual(phrases, ["ice cream"])
        self.assertEqual(tokenizer.calls[0][0], "ice cream shop")
        self.assertEqual(
            tokenizer.calls[0][1],
            {
                "return_tensors": "pt",
                "return_offsets_mapping": True,
                "return_special_tokens_mask": True,
                "truncation": True,
                "max_length": 512,
            },
        )

    async def test_extract_menu_phrases_excludes_non_food_and_special_tokens(self) -> None:
        service = QueryPreprocessService()
        tokenizer = FakeTokenizer(
            offset_mapping=[[(0, 0), (0, 4), (5, 9), (0, 0)]],
            special_tokens_mask=[[1, 0, 0, 1]],
        )
        model = FakeModel(
            predicted_ids=[28, 28, 0, 28],
        )

        with patch(
            "app.services.query_preprocess_service._load_menu_ner_components",
            return_value=(tokenizer, model, FakeTorch()),
        ):
            phrases = await service.extract_menu_phrases("cake cafe")

        self.assertEqual(phrases, ["cake"])

    async def test_extract_menu_phrases_preserves_multiple_food_spans_in_order(self) -> None:
        service = QueryPreprocessService()
        tokenizer = FakeTokenizer(
            offset_mapping=[[(0, 0), (0, 4), (5, 8), (9, 12), (0, 0)]],
            special_tokens_mask=[[1, 0, 0, 0, 1]],
        )
        model = FakeModel(
            predicted_ids=[299, 28, 0, 178, 299],
        )

        with patch(
            "app.services.query_preprocess_service._load_menu_ner_components",
            return_value=(tokenizer, model, FakeTorch()),
        ):
            phrases = await service.extract_menu_phrases("cake and pie")

        self.assertEqual(phrases, ["cake", "pie"])

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


class QueryPreprocessServiceLoaderTest(unittest.TestCase):
    def tearDown(self) -> None:
        _load_menu_ner_components.cache_clear()

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
        ):
            loaded_tokenizer, loaded_model, torch = _load_menu_ner_components()

        self.assertIs(loaded_tokenizer, tokenizer)
        self.assertIs(loaded_model, model)
        self.assertIs(torch, fake_torch)
        self.assertEqual(load_local.call_count, 2)
        self.assertEqual(
            load_local.call_args_list[0].args,
            (model_path, fake_auto_tokenizer, fake_bert_model),
        )
        self.assertEqual(
            load_local.call_args_list[1].args,
            (model_path, fake_auto_tokenizer, fake_bert_model),
        )
        download_components.assert_called_once_with(
            model_path,
            "hf-test-token",
            fake_auto_tokenizer,
            fake_bert_model,
        )
        self.assertEqual(tokenizer.source, str(model_path))
        self.assertEqual(model.source, str(model_path))
        self.assertEqual(model.to_calls, ["cpu"])
        self.assertTrue(model.eval_called)
