from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any
from urllib.parse import unquote, urlparse


ROOT_DIR = Path(__file__).resolve().parents[1]
DEFAULT_INPUT_PATH = ROOT_DIR / "data" / "cafe_enriched.json"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Rewrite thumbnail_url/image_url values in cafe_enriched.json. "
            "Default output is key-only format like cafes/<cafe_id>/images/03.jpeg."
        )
    )
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT_PATH, help="Input JSON file path")
    parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help="Output JSON file path. If omitted, input file is overwritten.",
    )
    parser.add_argument(
        "--cloudfront-base",
        type=str,
        default=None,
        help="Optional CloudFront base URL. Example: https://d111111abcdef8.cloudfront.net",
    )
    parser.add_argument("--dry-run", action="store_true", help="Show summary only, do not write file")
    return parser.parse_args()


def extract_key(url_or_key: str) -> str | None:
    text = url_or_key.strip()
    if not text:
        return None

    parsed = urlparse(text)
    if parsed.scheme and parsed.netloc:
        candidate = unquote(parsed.path).lstrip("/")
    else:
        candidate = unquote(text.split("?", 1)[0]).lstrip("/")

    if not candidate:
        return None

    marker = "cafes/"
    marker_index = candidate.find(marker)
    if marker_index >= 0:
        return candidate[marker_index:]
    return candidate


def build_output_value(original: Any, *, cloudfront_base: str | None) -> Any:
    if original is None:
        return None
    if not isinstance(original, str):
        return original

    key = extract_key(original)
    if not key:
        return original

    if cloudfront_base:
        return f"{cloudfront_base.rstrip('/')}/{key}"
    return key


def rewrite_document(rows: list[dict[str, Any]], *, cloudfront_base: str | None) -> tuple[int, int]:
    scanned = 0
    changed = 0

    for row in rows:
        cafes = row.get("cafes")
        if isinstance(cafes, dict) and "thumbnail_url" in cafes:
            scanned += 1
            old_value = cafes.get("thumbnail_url")
            new_value = build_output_value(old_value, cloudfront_base=cloudfront_base)
            if new_value != old_value:
                cafes["thumbnail_url"] = new_value
                changed += 1

        images = row.get("cafe_images")
        if not isinstance(images, list):
            continue

        for image in images:
            if not isinstance(image, dict) or "image_url" not in image:
                continue
            scanned += 1
            old_value = image.get("image_url")
            new_value = build_output_value(old_value, cloudfront_base=cloudfront_base)
            if new_value != old_value:
                image["image_url"] = new_value
                changed += 1

    return scanned, changed


def main() -> None:
    args = parse_args()
    input_path = args.input
    output_path = args.output or input_path

    if not input_path.exists():
        raise FileNotFoundError(f"Input file does not exist: {input_path}")

    raw_data = json.loads(input_path.read_text(encoding="utf-8"))
    if not isinstance(raw_data, list):
        raise ValueError(f"Expected top-level JSON array in {input_path}")

    scanned, changed = rewrite_document(raw_data, cloudfront_base=args.cloudfront_base)
    print(f"Scanned URLs: {scanned}")
    print(f"Changed URLs: {changed}")
    print(f"Mode: {'cloudfront' if args.cloudfront_base else 'key-only'}")

    if args.dry_run:
        print("Dry run mode enabled, no file written.")
        return

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(raw_data, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Written: {output_path}")


if __name__ == "__main__":
    main()
