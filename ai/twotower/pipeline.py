"""End-to-end positive-only two-tower pipeline."""

from __future__ import annotations

from dataclasses import asdict
import json
from pathlib import Path

import numpy as np
import pandas as pd
import torch
from torch.utils.data import DataLoader

from twotower.config import AppConfig
from twotower.metrics import compute_retrieval_metrics
from twotower.modeling import (
    FeatureBundle,
    PositiveOnlyTwoTowerModel,
    PositivePreferenceDataset,
    build_feature_bundle,
)
from twotower.preprocessing import (
    assign_preferred_cafe_ids,
    build_cafe_profiles,
    build_interaction_pairs,
    build_user_profiles,
    build_user_splits,
    load_crawl_items,
    load_prepared_artifacts,
    load_survey_dataframe,
    save_prepared_artifacts,
)
from twotower.text import AutoTextEncoder


class PositiveOnlyTwoTowerPipeline:
    """Coordinator for prepare/train/evaluate stages."""

    def __init__(self, config: AppConfig | None = None) -> None:
        self.config = config or AppConfig()
        self.config.ensure_output_dirs()
        self._resolved_device: torch.device | None = None

    def _resolve_device(self) -> torch.device:
        if self._resolved_device is not None:
            return self._resolved_device

        requested = self.config.training.device
        if requested == "cpu":
            self._resolved_device = torch.device("cpu")
            return self._resolved_device

        if requested in {"auto", "cuda"}:
            if torch.cuda.is_available():
                try:
                    torch.zeros(1, device="cuda")
                    self._resolved_device = torch.device("cuda")
                    self.config.training.device = "cuda"
                    return self._resolved_device
                except Exception as exc:
                    print(f"CUDA is not usable in this environment. Falling back to CPU. Detail: {exc}")
            elif requested == "cuda":
                print("CUDA was explicitly requested but is not available. Falling back to CPU.")

        self._resolved_device = torch.device("cpu")
        self.config.training.device = "cpu"
        return self._resolved_device

    def write_scaffold_manifest(self) -> Path:
        """Persist a manifest describing the planned artifacts."""
        manifest_path = self.config.data.reports_dir / "scaffold_manifest.json"
        payload = {
            "stage": "scaffold",
            "survey_csv": str(self.config.data.survey_csv),
            "crawl_dir": str(self.config.data.crawl_dir),
            "plan_markdown": str(self.config.data.plan_markdown),
            "output_dir": str(self.config.data.output_dir),
            "training": asdict(self.config.training),
            "text": asdict(self.config.text),
            "planned_artifacts": [
                str(self.config.data.user_profile_path),
                str(self.config.data.cafe_profile_path),
                str(self.config.data.interaction_pairs_path),
                str(self.config.data.user_splits_path),
                str(self.config.data.feature_bundle_path),
                str(self.config.data.model_checkpoint_path),
                str(self.config.data.metrics_path),
            ],
        }
        manifest_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
        return manifest_path

    def _prepared_exists(self) -> bool:
        return all(
            path.exists()
            for path in [
                self.config.data.user_profile_path,
                self.config.data.cafe_profile_path,
                self.config.data.interaction_pairs_path,
                self.config.data.user_splits_path,
            ]
        )

    def _load_prepared(self) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
        return load_prepared_artifacts(
            user_path=self.config.data.user_profile_path,
            cafe_path=self.config.data.cafe_profile_path,
            interaction_path=self.config.data.interaction_pairs_path,
            split_path=self.config.data.user_splits_path,
        )

    def prepare_data(self) -> None:
        survey_df = load_survey_dataframe(self.config.data.survey_csv)
        user_df = build_user_profiles(survey_df)

        crawl_items = load_crawl_items(self.config.data.crawl_dir)
        if not crawl_items:
            raise FileNotFoundError(f"No crawl JSON files found in {self.config.data.crawl_dir}")
        cafe_df = build_cafe_profiles(crawl_items)

        matching_encoder = AutoTextEncoder(
            backend=self.config.text.backend,
            model_name=self.config.text.model_name,
            allow_model_download=self.config.text.allow_model_download,
            tfidf_max_features=self.config.text.tfidf_max_features,
            svd_components=self.config.text.svd_components,
            random_seed=self.config.training.random_seed,
            device="cuda" if self._resolve_device().type == "cuda" else "cpu",
        )
        user_df = assign_preferred_cafe_ids(user_df, cafe_df, encoder=matching_encoder, top_k=3)
        interaction_df = build_interaction_pairs(user_df)
        split_df = build_user_splits(
            user_df["user_id"].tolist(),
            train_ratio=self.config.training.train_ratio,
            val_ratio=self.config.training.val_ratio,
            random_seed=self.config.training.random_seed,
        )

        save_prepared_artifacts(
            user_df=user_df,
            cafe_df=cafe_df,
            interaction_df=interaction_df,
            split_df=split_df,
            user_path=self.config.data.user_profile_path,
            cafe_path=self.config.data.cafe_profile_path,
            interaction_path=self.config.data.interaction_pairs_path,
            split_path=self.config.data.user_splits_path,
        )

        summary = {
            "survey_rows": int(len(user_df)),
            "cafe_rows": int(len(cafe_df)),
            "interaction_rows": int(len(interaction_df)),
            "matching_encoder": asdict(matching_encoder.info),
        }
        summary_path = self.config.data.reports_dir / "prepare_summary.json"
        summary_path.write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")
        print(f"Prepared data written to {self.config.data.prepared_dir}")

    def _ensure_prepared(self) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
        if not self._prepared_exists():
            self.prepare_data()
        return self._load_prepared()

    def _build_or_load_feature_bundle(self) -> FeatureBundle:
        if self.config.data.feature_bundle_path.exists():
            payload = torch.load(self.config.data.feature_bundle_path, map_location="cpu", weights_only=False)
            return FeatureBundle.from_dict(payload)

        user_df, cafe_df, _, split_df = self._ensure_prepared()
        bundle = build_feature_bundle(user_df=user_df, cafe_df=cafe_df, split_df=split_df, config=self.config)
        torch.save(bundle.to_dict(), self.config.data.feature_bundle_path)
        info_path = self.config.data.reports_dir / "text_encoder_info.json"
        info_path.write_text(json.dumps(bundle.text_encoder_info, indent=2, ensure_ascii=False), encoding="utf-8")
        return bundle

    @staticmethod
    def _user_batch(bundle: FeatureBundle, user_indices: np.ndarray, device: torch.device) -> dict[str, torch.Tensor]:
        return {
            "menu_ids": torch.as_tensor(bundle.user_menu_ids[user_indices], dtype=torch.long, device=device),
            "mood_multihot": torch.as_tensor(bundle.user_mood_multihot[user_indices], dtype=torch.float32, device=device),
            "nickname_bucket_ids": torch.as_tensor(
                bundle.user_nickname_buckets[user_indices], dtype=torch.long, device=device
            ),
            "email_bucket_ids": torch.as_tensor(bundle.user_email_buckets[user_indices], dtype=torch.long, device=device),
            "domain_bucket_ids": torch.as_tensor(bundle.user_domain_buckets[user_indices], dtype=torch.long, device=device),
            "preferred_cafe_ids": torch.as_tensor(
                bundle.user_preferred_cafe_indices[user_indices], dtype=torch.long, device=device
            ),
        }

    @staticmethod
    def _full_cafe_tensors(bundle: FeatureBundle, device: torch.device) -> tuple[torch.Tensor, torch.Tensor]:
        text_features = torch.as_tensor(bundle.cafe_text_features, dtype=torch.float32, device=device)
        struct_features = torch.as_tensor(bundle.cafe_struct_features, dtype=torch.float32, device=device)
        return text_features, struct_features

    def _compute_embeddings(
        self,
        *,
        model: PositiveOnlyTwoTowerModel,
        bundle: FeatureBundle,
        device: torch.device,
    ) -> tuple[np.ndarray, np.ndarray]:
        model.eval()
        with torch.no_grad():
            user_batch = self._user_batch(bundle, np.arange(len(bundle.user_ids)), device)
            cafe_text, cafe_struct = self._full_cafe_tensors(bundle, device)
            user_embeddings = model.get_user_embeddings(user_batch).cpu().numpy().astype(np.float32)
            cafe_embeddings = model.get_cafe_embeddings(
                text_features=cafe_text,
                struct_features=cafe_struct,
            ).cpu().numpy().astype(np.float32)
        return user_embeddings, cafe_embeddings

    def _evaluate_split(
        self,
        *,
        model: PositiveOnlyTwoTowerModel,
        bundle: FeatureBundle,
        split_indices: np.ndarray,
        device: torch.device,
        k: int = 10,
    ) -> tuple[dict[str, float], pd.DataFrame]:
        if len(split_indices) == 0:
            return {f"recall@{k}": 0.0, f"mrr@{k}": 0.0}, pd.DataFrame()

        user_embeddings, cafe_embeddings = self._compute_embeddings(model=model, bundle=bundle, device=device)
        relevant = [
            [int(cafe_index) - 1 for cafe_index in bundle.positive_cafe_indices[user_index] if int(cafe_index) > 0]
            for user_index in split_indices
        ]
        metrics, ranked = compute_retrieval_metrics(
            user_embeddings=user_embeddings[split_indices],
            cafe_embeddings=cafe_embeddings,
            relevant_indices=relevant,
            k=k,
        )

        recommendation_rows: list[dict[str, object]] = []
        for local_index, user_index in enumerate(split_indices):
            top_k_indices = ranked[local_index, :k].tolist()
            recommendation_rows.append(
                {
                    "user_id": bundle.user_ids[int(user_index)],
                    "recommended_cafe_ids": [bundle.cafe_ids[int(cafe_index)] for cafe_index in top_k_indices],
                    "positive_cafe_ids": [
                        bundle.cafe_ids[int(cafe_index)]
                        for cafe_index in relevant[local_index]
                        if 0 <= int(cafe_index) < len(bundle.cafe_ids)
                    ],
                }
            )
        return metrics, pd.DataFrame.from_records(recommendation_rows)

    def train(self) -> None:
        device = self._resolve_device()
        bundle = self._build_or_load_feature_bundle()
        model = PositiveOnlyTwoTowerModel(bundle=bundle, config=self.config).to(device)
        optimizer = torch.optim.AdamW(
            model.parameters(),
            lr=self.config.training.learning_rate,
            weight_decay=self.config.training.weight_decay,
        )
        criterion = torch.nn.CrossEntropyLoss()
        dataset = PositivePreferenceDataset(bundle.train_user_indices, bundle.positive_cafe_indices)
        dataloader = DataLoader(
            dataset,
            batch_size=min(self.config.training.batch_size, max(1, len(dataset))),
            shuffle=True,
        )
        full_cafe_text, full_cafe_struct = self._full_cafe_tensors(bundle, device)

        best_state: dict[str, torch.Tensor] | None = None
        best_val_recall = float("-inf")
        best_val_metrics: dict[str, float] = {}
        history: list[dict[str, float]] = []
        patience = 0

        for epoch in range(self.config.training.epochs):
            dataset.set_epoch(epoch)
            model.train()
            epoch_losses: list[float] = []

            for user_indices, cafe_indices in dataloader:
                user_index_array = user_indices.cpu().numpy()
                user_batch = self._user_batch(bundle, user_index_array, device)
                batch_cafe_indices = cafe_indices.to(device)
                cafe_text_batch = full_cafe_text[batch_cafe_indices]
                cafe_struct_batch = full_cafe_struct[batch_cafe_indices]

                optimizer.zero_grad()
                user_embeddings, cafe_embeddings = model(
                    user_batch=user_batch,
                    cafe_text_features=cafe_text_batch,
                    cafe_struct_features=cafe_struct_batch,
                )
                logits = user_embeddings @ cafe_embeddings.T / self.config.training.temperature
                labels = torch.arange(len(user_embeddings), device=device)
                loss = (criterion(logits, labels) + criterion(logits.T, labels)) / 2.0
                loss.backward()
                optimizer.step()
                epoch_losses.append(float(loss.item()))

            val_metrics, _ = self._evaluate_split(
                model=model,
                bundle=bundle,
                split_indices=bundle.val_user_indices,
                device=device,
                k=10,
            )
            epoch_summary = {"epoch": epoch + 1, "train_loss": float(np.mean(epoch_losses)), **val_metrics}
            history.append(epoch_summary)
            print(
                f"epoch={epoch + 1} loss={epoch_summary['train_loss']:.4f} "
                f"recall@10={val_metrics['recall@10']:.4f} mrr@10={val_metrics['mrr@10']:.4f}"
            )

            if val_metrics["recall@10"] > best_val_recall:
                best_val_recall = val_metrics["recall@10"]
                best_val_metrics = val_metrics
                best_state = {key: value.detach().cpu() for key, value in model.state_dict().items()}
                patience = 0
            else:
                patience += 1
                if patience >= self.config.training.early_stopping_patience:
                    break

        if best_state is not None:
            model.load_state_dict(best_state)

        user_embeddings, cafe_embeddings = self._compute_embeddings(model=model, bundle=bundle, device=device)
        np.save(self.config.data.user_embeddings_path, user_embeddings)
        np.save(self.config.data.cafe_embeddings_path, cafe_embeddings)

        checkpoint = {
            "model_state_dict": model.state_dict(),
            "training_config": asdict(self.config.training),
            "text_config": asdict(self.config.text),
            "best_val_metrics": best_val_metrics,
            "history": history,
        }
        torch.save(checkpoint, self.config.data.model_checkpoint_path)
        print(f"Model checkpoint written to {self.config.data.model_checkpoint_path}")

    def evaluate(self) -> None:
        device = self._resolve_device()
        bundle = self._build_or_load_feature_bundle()
        if not self.config.data.model_checkpoint_path.exists():
            self.train()

        checkpoint = torch.load(self.config.data.model_checkpoint_path, map_location="cpu", weights_only=False)
        model = PositiveOnlyTwoTowerModel(bundle=bundle, config=self.config)
        model.load_state_dict(checkpoint["model_state_dict"])

        model.to(device)
        val_metrics, _ = self._evaluate_split(
            model=model,
            bundle=bundle,
            split_indices=bundle.val_user_indices,
            device=device,
            k=10,
        )
        test_metrics, recommendations = self._evaluate_split(
            model=model,
            bundle=bundle,
            split_indices=bundle.test_user_indices,
            device=device,
            k=10,
        )

        metrics_payload = {
            "validation": val_metrics,
            "test": test_metrics,
            "best_val_metrics": checkpoint.get("best_val_metrics", {}),
            "training_history": checkpoint.get("history", []),
            "text_encoder_info": bundle.text_encoder_info,
            "num_users": len(bundle.user_ids),
            "num_cafes": len(bundle.cafe_ids),
        }
        self.config.data.metrics_path.write_text(
            json.dumps(metrics_payload, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
        if not recommendations.empty:
            recommendations = recommendations.copy()
            for column in ["recommended_cafe_ids", "positive_cafe_ids"]:
                recommendations[column] = recommendations[column].map(
                    lambda values: json.dumps(values, ensure_ascii=False)
                )
            recommendations.to_parquet(self.config.data.recommendations_path, index=False)
        print(f"Metrics written to {self.config.data.metrics_path}")

    def export_cafe_vectors_json(self) -> Path:
        if not self.config.data.feature_bundle_path.exists():
            raise FileNotFoundError(
                f"Feature bundle not found at {self.config.data.feature_bundle_path}. "
                "Run train first or provide the matching output directory."
            )
        if not self.config.data.cafe_embeddings_path.exists():
            raise FileNotFoundError(
                f"Cafe embeddings not found at {self.config.data.cafe_embeddings_path}. "
                "Run train first or provide the matching output directory."
            )

        crawl_items = load_crawl_items(self.config.data.crawl_dir)
        if not crawl_items:
            raise FileNotFoundError(f"No crawl JSON files found in {self.config.data.crawl_dir}")
        crawl_cafe_df = build_cafe_profiles(crawl_items)[["cafe_id", "name"]].drop_duplicates(subset=["cafe_id"])
        crawl_name_by_id = crawl_cafe_df.set_index("cafe_id")["name"].to_dict()

        bundle_payload = torch.load(self.config.data.feature_bundle_path, map_location="cpu", weights_only=False)
        bundle = FeatureBundle.from_dict(bundle_payload)
        cafe_embeddings = np.load(self.config.data.cafe_embeddings_path)

        if cafe_embeddings.ndim != 2:
            raise ValueError(
                f"Expected a 2D cafe embedding matrix, but found shape {cafe_embeddings.shape}."
            )
        if len(bundle.cafe_ids) != int(cafe_embeddings.shape[0]):
            raise ValueError(
                "Cafe embedding row count does not match feature bundle cafe_ids. "
                f"bundle={len(bundle.cafe_ids)} embeddings={cafe_embeddings.shape[0]}"
            )

        bundle_ids = set(bundle.cafe_ids)
        crawl_ids = set(crawl_name_by_id)
        missing_from_crawl = sorted(bundle_ids - crawl_ids)
        extra_in_crawl = sorted(crawl_ids - bundle_ids)
        unnamed_ids = sorted(
            cafe_id for cafe_id in bundle.cafe_ids if not str(crawl_name_by_id.get(cafe_id, "")).strip()
        )

        if missing_from_crawl or extra_in_crawl:
            details: list[str] = []
            if missing_from_crawl:
                details.append(f"missing_in_success={missing_from_crawl[:5]}")
            if extra_in_crawl:
                details.append(f"extra_in_success={extra_in_crawl[:5]}")
            raise ValueError(
                "success crawl data and trained cafe ids do not match. "
                + " ".join(details)
            )
        if unnamed_ids:
            raise ValueError(f"Found cafes without a name in success crawl data: {unnamed_ids[:5]}")

        if self.config.data.cafe_profile_path.exists():
            prepared_cafe_df = pd.read_parquet(self.config.data.cafe_profile_path)
            prepared_ids = prepared_cafe_df["cafe_id"].astype(str).tolist()
            if prepared_ids != bundle.cafe_ids:
                raise ValueError(
                    "Prepared cafe_profile ordering does not match feature bundle cafe_ids. "
                    "Use artifacts produced from the same training run."
                )

        records = [
            {
                "cafe_id": cafe_id,
                "cafe_name": str(crawl_name_by_id[cafe_id]),
                "cafe_vector": cafe_embeddings[index].astype(float).tolist(),
            }
            for index, cafe_id in enumerate(bundle.cafe_ids)
        ]

        export_path = self.config.data.cafe_vectors_json_path
        export_path.write_text(json.dumps(records, indent=2, ensure_ascii=False), encoding="utf-8")
        print(f"Cafe vectors written to {export_path}")
        return export_path

    def export_user_vectors_json(self) -> Path:
        if not self.config.data.feature_bundle_path.exists():
            raise FileNotFoundError(
                f"Feature bundle not found at {self.config.data.feature_bundle_path}. "
                "Run train first or provide the matching output directory."
            )
        if not self.config.data.user_embeddings_path.exists():
            raise FileNotFoundError(
                f"User embeddings not found at {self.config.data.user_embeddings_path}. "
                "Run train first or provide the matching output directory."
            )
        if not self.config.data.user_profile_path.exists():
            raise FileNotFoundError(
                f"Prepared user profile not found at {self.config.data.user_profile_path}. "
                "Run prepare-data/train first or provide the matching output directory."
            )

        bundle_payload = torch.load(self.config.data.feature_bundle_path, map_location="cpu", weights_only=False)
        bundle = FeatureBundle.from_dict(bundle_payload)
        user_embeddings = np.load(self.config.data.user_embeddings_path)
        user_profile_df = pd.read_parquet(self.config.data.user_profile_path)

        if user_embeddings.ndim != 2:
            raise ValueError(
                f"Expected a 2D user embedding matrix, but found shape {user_embeddings.shape}."
            )
        if len(bundle.user_ids) != int(user_embeddings.shape[0]):
            raise ValueError(
                "User embedding row count does not match feature bundle user_ids. "
                f"bundle={len(bundle.user_ids)} embeddings={user_embeddings.shape[0]}"
            )

        prepared_ids = user_profile_df["user_id"].astype(str).tolist()
        if prepared_ids != bundle.user_ids:
            raise ValueError(
                "Prepared user_profile ordering does not match feature bundle user_ids. "
                "Use artifacts produced from the same training run."
            )

        missing_columns = [column for column in ["user_id", "nickname", "email"] if column not in user_profile_df.columns]
        if missing_columns:
            raise ValueError(f"user_profile is missing required columns: {missing_columns}")

        records = [
            {
                "user_id": str(row["user_id"]),
                "nickname": str(row["nickname"]),
                "email": str(row["email"]),
                "user_vector": user_embeddings[index].astype(float).tolist(),
            }
            for index, (_, row) in enumerate(user_profile_df.iterrows())
        ]

        export_path = self.config.data.user_vectors_json_path
        export_path.write_text(json.dumps(records, indent=2, ensure_ascii=False), encoding="utf-8")
        print(f"User vectors written to {export_path}")
        return export_path

    def run_all(self) -> None:
        self.prepare_data()
        self.train()
        self.evaluate()
