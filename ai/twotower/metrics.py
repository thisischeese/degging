"""Retrieval metrics for positive-only evaluation."""

from __future__ import annotations

import numpy as np


def recall_at_k(ranked_indices: np.ndarray, relevant_indices: set[int], k: int) -> float:
    top_k = ranked_indices[:k]
    if not relevant_indices:
        return 0.0
    hits = sum(1 for index in top_k if int(index) in relevant_indices)
    return hits / float(len(relevant_indices))


def reciprocal_rank_at_k(ranked_indices: np.ndarray, relevant_indices: set[int], k: int) -> float:
    for position, index in enumerate(ranked_indices[:k], start=1):
        if int(index) in relevant_indices:
            return 1.0 / float(position)
    return 0.0


def compute_retrieval_metrics(
    *,
    user_embeddings: np.ndarray,
    cafe_embeddings: np.ndarray,
    relevant_indices: list[list[int]],
    k: int = 10,
) -> tuple[dict[str, float], np.ndarray]:
    scores = user_embeddings @ cafe_embeddings.T
    ranked = np.argsort(-scores, axis=1)

    recalls: list[float] = []
    reciprocal_ranks: list[float] = []
    for row_index, positives in enumerate(relevant_indices):
        relevant = set(int(value) for value in positives)
        recalls.append(recall_at_k(ranked[row_index], relevant, k))
        reciprocal_ranks.append(reciprocal_rank_at_k(ranked[row_index], relevant, k))

    metrics = {
        f"recall@{k}": float(np.mean(recalls) if recalls else 0.0),
        f"mrr@{k}": float(np.mean(reciprocal_ranks) if reciprocal_ranks else 0.0),
    }
    return metrics, ranked
