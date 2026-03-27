from fastapi import APIRouter, Depends

from app.models.onboarding import OnboardingRequest, OnboardingResponse, OnboardingResponseData
from app.services.onboarding_service import OnboardingResult, OnboardingService

router = APIRouter(prefix="/onboarding", tags=["onboarding"])


def get_onboarding_service() -> OnboardingService:
    return OnboardingService()


@router.post(
    "",
    response_model=OnboardingResponse,
    summary="Create or update a user preference vector from onboarding inputs",
    description=(
        "Compute a 64-dim preference vector with the trained two-tower user tower, "
        "store it in PostgreSQL user_preference, and return the saved timestamp."
    ),
)
async def onboarding(
    request: OnboardingRequest,
    service: OnboardingService = Depends(get_onboarding_service),
) -> OnboardingResponse:
    result: OnboardingResult = await service.onboard(request)
    return OnboardingResponse(
        status="success",
        message="Onboarding completed successfully.",
        data=OnboardingResponseData(
            user_id=result.user_id,
            updated_at=result.updated_at,
        ),
    )
