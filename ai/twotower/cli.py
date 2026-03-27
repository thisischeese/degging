"""Command-line entrypoint for the twotower scaffold."""

from __future__ import annotations

import argparse
from pathlib import Path

from twotower.config import AppConfig
from twotower.pipeline import PositiveOnlyTwoTowerPipeline


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="twotower",
        description="Positive-only two-tower cafe recommendation pipeline.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("artifacts"),
        help="Directory for generated artifacts.",
    )
    parser.add_argument(
        "--survey-csv",
        type=Path,
        default=None,
        help="Override the default Google Form CSV path.",
    )
    parser.add_argument(
        "--crawl-dir",
        type=Path,
        default=None,
        help="Override the default crawl JSON directory.",
    )
    parser.add_argument(
        "--text-backend",
        default=None,
        choices=["auto", "sentence-transformer", "tfidf"],
        help="Text encoder backend for matching and cafe text features.",
    )
    parser.add_argument(
        "--allow-model-download",
        action="store_true",
        help="Allow sentence-transformers to download the model if it is not already cached.",
    )
    parser.add_argument(
        "--device",
        default=None,
        choices=["auto", "cpu", "cuda"],
        help="Torch device to use for encoding and training.",
    )
    parser.add_argument(
        "--epochs",
        type=int,
        default=None,
        help="Override the number of training epochs.",
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=None,
        help="Override the training batch size.",
    )
    parser.add_argument(
        "--learning-rate",
        type=float,
        default=None,
        help="Override the optimizer learning rate.",
    )
    parser.add_argument(
        "--model-name",
        default=None,
        help="Sentence-transformers model name to use when the backend is sentence-transformer or auto.",
    )

    subparsers = parser.add_subparsers(dest="command", required=True)
    subparsers.add_parser("scaffold-manifest", help="Write scaffold manifest artifacts.")
    subparsers.add_parser("prepare-data", help="Prepare user/cafe profiles and interaction pairs.")
    subparsers.add_parser("train", help="Train the two-tower model.")
    subparsers.add_parser("evaluate", help="Evaluate retrieval metrics.")
    subparsers.add_parser("export-cafe-vectors", help="Export cafe_id, cafe_name, cafe_vector JSON for serving.")
    subparsers.add_parser("export-user-vectors", help="Export user_id, nickname, email, user_vector JSON for serving.")
    subparsers.add_parser("run-all", help="Run prepare/train/evaluate in sequence.")
    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    config = AppConfig()
    config.data.output_dir = args.output_dir
    if args.survey_csv is not None:
        config.data.survey_csv = args.survey_csv
    if args.crawl_dir is not None:
        config.data.crawl_dir = args.crawl_dir
    if args.text_backend is not None:
        config.text.backend = args.text_backend
    if args.allow_model_download:
        config.text.allow_model_download = True
    if args.device is not None:
        config.training.device = args.device
    if args.epochs is not None:
        config.training.epochs = args.epochs
    if args.batch_size is not None:
        config.training.batch_size = args.batch_size
    if args.learning_rate is not None:
        config.training.learning_rate = args.learning_rate
    if args.model_name is not None:
        config.text.model_name = args.model_name
    pipeline = PositiveOnlyTwoTowerPipeline(config=config)

    if args.command == "scaffold-manifest":
        manifest = pipeline.write_scaffold_manifest()
        print(f"Scaffold manifest written to {manifest}")
        return
    if args.command == "prepare-data":
        pipeline.prepare_data()
        return
    if args.command == "train":
        pipeline.train()
        return
    if args.command == "evaluate":
        pipeline.evaluate()
        return
    if args.command == "export-cafe-vectors":
        pipeline.export_cafe_vectors_json()
        return
    if args.command == "export-user-vectors":
        pipeline.export_user_vectors_json()
        return
    if args.command == "run-all":
        pipeline.run_all()
        return

    parser.error(f"Unknown command: {args.command}")
