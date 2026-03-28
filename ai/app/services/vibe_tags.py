from __future__ import annotations

DEFAULT_VIBE_TAG_ID = "e747e844-db71-42ea-81cf-c25d510672b2"

VIBE_TAG_LABELS: dict[str, str] = {
    "7ab663df-31be-43f8-b06a-2e8979806d89": "\uc6b0\ub4dc\ud1a4/\ub530\ub73b\ud568",
    "4ada6e46-3d5b-4ac8-abf9-9479abb35cfc": "\uc2dd\ubb3c\uc6d0/\ud50c\ub79c\ud14c\ub9ac\uc5b4",
    "c35facb1-f2ae-42aa-8234-522f6ae3352b": "\ud799\ud55c",
    "e747e844-db71-42ea-81cf-c25d510672b2": "\uc870\uc6a9\ud55c/\ucc28\ubd84\ud55c",
    "9b71769c-2293-4e06-bf37-f1fbf33c2853": "\ud0c1 \ud2b8\uc778/\ubdf0 \uc88b\uc740",
}


def resolve_vibe_label(tag_id: object) -> str | None:
    normalized_tag_id = str(tag_id or "").strip()
    if not normalized_tag_id:
        return None
    return VIBE_TAG_LABELS.get(normalized_tag_id)


def resolve_vibe_labels(tag_ids: list[object]) -> list[str]:
    resolved_labels: list[str] = []
    seen_labels: set[str] = set()
    for tag_id in tag_ids:
        label = resolve_vibe_label(tag_id)
        if label is None or label in seen_labels:
            continue
        seen_labels.add(label)
        resolved_labels.append(label)
    return resolved_labels
