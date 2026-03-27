from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from app.db.postgresql import get_pg_pool
from app.models.onboarding import OnboardingRequest
from app.services.onboarding_inference import OnboardingInferenceEngine, get_onboarding_inference_engine
from app.services.preference_vector import upsert_user_preference_vector


@dataclass(slots=True)
class OnboardingResult:
    user_id: UUID
    updated_at: datetime


class OnboardingService:
    def __init__(
        self,
        inference_engine: OnboardingInferenceEngine | None = None,
    ) -> None:
        self._inference_engine = inference_engine or get_onboarding_inference_engine()

    async def onboard(self, request: OnboardingRequest) -> OnboardingResult:
        preference_vector = self._inference_engine.vectorize_user(
            nickname=request.nickname,
            email=request.email,
            favorite_menus=request.favorite_menus,
            mood_tags=request.mood_tags,
            cafes=request.cafes,
        )

        pool = get_pg_pool()
        async with pool.acquire() as conn:
            async with conn.transaction():
                updated_at = await upsert_user_preference_vector(
                    conn,
                    request.user_id,
                    preference_vector,
                )

        return OnboardingResult(
            user_id=request.user_id,
            updated_at=updated_at,
        )
