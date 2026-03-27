"""Text encoder utilities with offline-friendly fallback behavior."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from sklearn.decomposition import TruncatedSVD
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.preprocessing import normalize


@dataclass(slots=True)
class TextEncoderInfo:
    backend_requested: str
    backend_used: str
    output_dim: int
    model_name: str | None = None


class AutoTextEncoder:
    """Sentence-transformers first, TF-IDF + SVD fallback second."""

    def __init__(
        self,
        *,
        backend: str = "auto",
        model_name: str = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2",
        allow_model_download: bool = False,
        tfidf_max_features: int = 4096,
        svd_components: int = 64,
        random_seed: int = 42,
        device: str = "cpu",
    ) -> None:
        self.backend = backend
        self.model_name = model_name
        self.allow_model_download = allow_model_download
        self.tfidf_max_features = tfidf_max_features
        self.svd_components = svd_components
        self.random_seed = random_seed
        self.device = device

        self._model = None
        self._vectorizer: TfidfVectorizer | None = None
        self._svd: TruncatedSVD | None = None
        self.info = TextEncoderInfo(backend_requested=backend, backend_used="uninitialized", output_dim=0)

    def fit(self, texts: list[str]) -> "AutoTextEncoder":
        if self.backend in {"auto", "sentence-transformer"}:
            try:
                from sentence_transformers import SentenceTransformer

                try:
                    self._model = SentenceTransformer(
                        self.model_name,
                        device=self.device,
                        local_files_only=not self.allow_model_download,
                    )
                except Exception:
                    if self.device != "cpu":
                        self._model = SentenceTransformer(
                            self.model_name,
                            device="cpu",
                            local_files_only=not self.allow_model_download,
                        )
                    else:
                        raise
                output_dim = int(self._model.get_sentence_embedding_dimension())
                self.info = TextEncoderInfo(
                    backend_requested=self.backend,
                    backend_used="sentence-transformer",
                    output_dim=output_dim,
                    model_name=self.model_name,
                )
                return self
            except Exception:
                if self.backend == "sentence-transformer":
                    raise

        self._vectorizer = TfidfVectorizer(max_features=self.tfidf_max_features, ngram_range=(1, 2))
        sparse = self._vectorizer.fit_transform(texts)

        max_components = min(self.svd_components, sparse.shape[0] - 1, sparse.shape[1] - 1)
        if max_components >= 2:
            self._svd = TruncatedSVD(n_components=max_components, random_state=self.random_seed)
            dense = self._svd.fit_transform(sparse)
            output_dim = dense.shape[1]
            backend_used = "tfidf-svd"
        else:
            self._svd = None
            output_dim = sparse.shape[1]
            backend_used = "tfidf"

        self.info = TextEncoderInfo(
            backend_requested=self.backend,
            backend_used=backend_used,
            output_dim=output_dim,
            model_name=None,
        )
        return self

    def transform(self, texts: list[str]) -> np.ndarray:
        if self._model is not None:
            embeddings = self._model.encode(
                texts,
                show_progress_bar=False,
                convert_to_numpy=True,
                normalize_embeddings=True,
            )
            return embeddings.astype(np.float32)

        if self._vectorizer is None:
            raise RuntimeError("Text encoder must be fitted before calling transform().")

        sparse = self._vectorizer.transform(texts)
        if self._svd is not None:
            dense = self._svd.transform(sparse)
        else:
            dense = sparse.toarray()
        return normalize(dense.astype(np.float32))

    def fit_transform(self, texts: list[str]) -> np.ndarray:
        self.fit(texts)
        return self.transform(texts)
