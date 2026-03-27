from __future__ import annotations

import logging
from typing import Protocol
from uuid import UUID

logger = logging.getLogger(__name__)

EXPECTED_PREFERENCE_VECTOR_DIMENSIONS = 64

USER_PREFERENCE_QUERY = """
    SELECT preference_vector::text AS preference_vector
    FROM user_preference
    WHERE user_id = $1
"""


class SupportsFetchRow(Protocol):
    async def fetchrow(self, query: str, *args: object) -> object: ...


class UserPreferenceNotFoundError(Exception):
    """Raised when a user preference vector does not exist."""


class InvalidPreferenceVectorError(RuntimeError):
    """Raised when a stored preference vector is malformed."""


def to_vector_literal(vector: list[float]) -> str:
    return "[" + ",".join(str(value) for value in vector) + "]"


def parse_vector_literal(vector_literal: str) -> list[float]:
    normalized_literal = vector_literal.strip()
    if not normalized_literal or normalized_literal == "[]":
        return []
    if not (normalized_literal.startswith("[") and normalized_literal.endswith("]")):
        raise InvalidPreferenceVectorError(f"Invalid vector literal: {vector_literal}")

    values = normalized_literal[1:-1].strip()
    if not values:
        return []

    try:
        return [float(value.strip()) for value in values.split(",") if value.strip()]
    except ValueError as exc:
        raise InvalidPreferenceVectorError(
            f"Invalid numeric value in vector literal: {vector_literal}"
        ) from exc


def validate_vector_dimensions(
    vector: list[float],
    *,
    expected_dimensions: int | None = None,
) -> list[float]:
    if expected_dimensions is None:
        expected_dimensions = EXPECTED_PREFERENCE_VECTOR_DIMENSIONS

    if len(vector) != expected_dimensions:
        raise InvalidPreferenceVectorError(
            f"Expected vector({expected_dimensions}), got vector({len(vector)})"
        )
    return vector


async def fetch_user_preference_vector(
    conn: SupportsFetchRow,
    user_id: UUID,
    *,
    expected_dimensions: int | None = None,
) -> list[float]:
    if expected_dimensions is None:
        expected_dimensions = EXPECTED_PREFERENCE_VECTOR_DIMENSIONS

    row = await conn.fetchrow(USER_PREFERENCE_QUERY, user_id)
    if row is None:
        raise UserPreferenceNotFoundError(f"user_id={user_id} preference vector not found.")

    preference_vector_literal = row["preference_vector"]
    if preference_vector_literal is None:
        raise UserPreferenceNotFoundError(f"user_id={user_id} preference vector not found.")

    try:
        preference_vector = parse_vector_literal(preference_vector_literal)
        if not preference_vector:
            raise UserPreferenceNotFoundError(
                f"user_id={user_id} preference vector not found."
            )
        return validate_vector_dimensions(
            preference_vector,
            expected_dimensions=expected_dimensions,
        )
    except UserPreferenceNotFoundError:
        raise
    except InvalidPreferenceVectorError:
        logger.exception(
            "Invalid PostgreSQL preference vector for user_id=%s",
            user_id,
        )
        raise
