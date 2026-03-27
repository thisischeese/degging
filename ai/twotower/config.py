"""Configuration objects for the positive-only two-tower pipeline."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path


@dataclass(slots=True)
class DataPaths:
    survey_csv: Path = Path(r"C:\Users\SSAFY\Downloads\google_form.csv")
    crawl_dir: Path = Path(r"C:\Users\SSAFY\Downloads\crawling-backup\success")
    plan_markdown: Path = Path(r"C:\Users\SSAFY\Downloads\PLAN_degging.md")
    output_dir: Path = Path("artifacts")

    @property
    def prepared_dir(self) -> Path:
        return self.output_dir / "prepared"

    @property
    def models_dir(self) -> Path:
        return self.output_dir / "models"

    @property
    def reports_dir(self) -> Path:
        return self.output_dir / "reports"

    @property
    def serving_dir(self) -> Path:
        return self.output_dir / "serving"

    @property
    def user_profile_path(self) -> Path:
        return self.prepared_dir / "user_profile.parquet"

    @property
    def cafe_profile_path(self) -> Path:
        return self.prepared_dir / "cafe_profile.parquet"

    @property
    def interaction_pairs_path(self) -> Path:
        return self.prepared_dir / "interaction_pairs.parquet"

    @property
    def user_splits_path(self) -> Path:
        return self.prepared_dir / "user_splits.parquet"

    @property
    def feature_bundle_path(self) -> Path:
        return self.models_dir / "feature_bundle.pt"

    @property
    def model_checkpoint_path(self) -> Path:
        return self.models_dir / "two_tower_model.pt"

    @property
    def user_embeddings_path(self) -> Path:
        return self.models_dir / "user_embeddings.npy"

    @property
    def cafe_embeddings_path(self) -> Path:
        return self.models_dir / "cafe_embeddings.npy"

    @property
    def metrics_path(self) -> Path:
        return self.reports_dir / "metrics.json"

    @property
    def recommendations_path(self) -> Path:
        return self.reports_dir / "test_recommendations.parquet"

    @property
    def cafe_vectors_json_path(self) -> Path:
        return self.serving_dir / "cafe_vectors.json"

    @property
    def user_vectors_json_path(self) -> Path:
        return self.serving_dir / "user_vectors.json"


@dataclass(slots=True)
class TrainingConfig:
    batch_size: int = 32
    epochs: int = 30
    learning_rate: float = 1e-3
    weight_decay: float = 1e-4
    embedding_dim: int = 64
    hidden_dim: int = 256
    dropout: float = 0.2
    temperature: float = 0.07
    random_seed: int = 42
    menu_embedding_dim: int = 32
    id_embedding_dim: int = 16
    hash_bucket_size: int = 2048
    early_stopping_patience: int = 8
    train_ratio: float = 0.8
    val_ratio: float = 0.1
    device: str = "auto"


@dataclass(slots=True)
class TextEncoderConfig:
    backend: str = "auto"
    model_name: str = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
    allow_model_download: bool = False
    tfidf_max_features: int = 4096
    svd_components: int = 64


@dataclass(slots=True)
class AppConfig:
    data: DataPaths = field(default_factory=DataPaths)
    training: TrainingConfig = field(default_factory=TrainingConfig)
    text: TextEncoderConfig = field(default_factory=TextEncoderConfig)

    def ensure_output_dirs(self) -> None:
        """Create artifact directories used by future pipeline stages."""
        self.data.output_dir.mkdir(parents=True, exist_ok=True)
        self.data.prepared_dir.mkdir(parents=True, exist_ok=True)
        self.data.models_dir.mkdir(parents=True, exist_ok=True)
        self.data.reports_dir.mkdir(parents=True, exist_ok=True)
        self.data.serving_dir.mkdir(parents=True, exist_ok=True)
