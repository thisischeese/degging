from pydantic import BaseModel, ConfigDict, Field, RootModel, field_validator


class CafeCrawlingRequestItem(BaseModel):
    model_config = ConfigDict(extra="forbid")

    cafeId: str = Field(..., description="크롤링 대상 카페 ID")
    name: str = Field(..., description="네이버 플레이스 검색에 사용할 카페명")

    @field_validator("cafeId")
    @classmethod
    def validate_cafe_id(cls, value: str) -> str:
        stripped = value.strip()
        if not stripped:
            raise ValueError("cafeId must not be blank")
        return stripped

    @field_validator("name")
    @classmethod
    def validate_name(cls, value: str) -> str:
        stripped = value.strip()
        if not stripped:
            raise ValueError("name must not be blank")
        return stripped


class CafeCrawlingRequest(RootModel[list[CafeCrawlingRequestItem]]):
    pass


class CafeInfo(BaseModel):
    cafe_id: str
    bizes_id: str
    kakao_place_id: str
    name: str
    address: str | None = None
    road_address: str | None = None
    phone: str | None = None
    thumbnail_url: str | None = None
    status: str
    location: str | None = None
    cafe_intro: str
    franchise: bool
    brandName: str | None = None
    branchName: str | None = None


class CafeRatingStats(BaseModel):
    cafe_id: str
    review_count: int
    rating_sum: int
    solo_ratio: str
    date_ratio: str
    friends_ratio: str


class CafeImage(BaseModel):
    image_id: int
    image_url: str
    sort_order: int
    cafe_id: str


class CafeMenu(BaseModel):
    menu_id: int
    menu_name: str
    price: int | None = None
    menu_description: str | None = None
    cafe_id: str


class CafeBusinessHours(BaseModel):
    cafe_id: str
    mon_hours: str | None = None
    tues_hours: str | None = None
    wed_hours: str | None = None
    thur_hours: str | None = None
    fri_hours: str | None = None
    sat_hours: str | None = None
    sun_hours: str | None = None


class CafeVibeTag(BaseModel):
    cafe_vibe_tag_id: int
    tag_id: str
    cafe_id: str


class CafeReview(BaseModel):
    user_id: str
    user_review: str


class CafeCrawlingMergedItem(BaseModel):
    model_config = ConfigDict(extra="ignore")

    cafe_id: str
    cafes: CafeInfo
    cafe_rating_stats: CafeRatingStats
    cafe_images: list[CafeImage] = Field(default_factory=list)
    cafe_menus: list[CafeMenu] = Field(default_factory=list)
    cafe_business_hours: CafeBusinessHours
    cafe_vibe_tags: list[CafeVibeTag] = Field(default_factory=list)
    cafe_reviews: list[CafeReview] = Field(default_factory=list)


class CafeCrawlingResponse(BaseModel):
    items: list[CafeCrawlingMergedItem] = Field(default_factory=list)
    total: int
    missing_cafe_ids: list[str] = Field(default_factory=list)
