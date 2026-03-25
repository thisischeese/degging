package com.degging.be.cafe.dto.response.external;

import com.fasterxml.jackson.databind.PropertyNamingStrategies;
import com.fasterxml.jackson.databind.annotation.JsonNaming;
import lombok.Data;

import java.util.List;
import java.util.UUID;

/**
 * AI 크롤러로부터 수신하는 카페 개별 크롤링 결과 DTO (AiCrawlerResponse.items 항목)
 */
@Data
@JsonNaming(PropertyNamingStrategies.SnakeCaseStrategy.class)
public class AiCrawlerItemResponse {

    private UUID cafeId; // 카페 식별자
    private CafeInnerDto cafes; // 카페 기본 정보 (이름, 썸네일, 소개글 등)
    private CafeRatingStatsDto cafeRatingStats; // 평점 및 방문자 비율 통계
    private List<CafeImageDto> cafeImages; // 카페 관련 이미지 목록
    private List<CafeMenuDto> cafeMenus; // 카페 메뉴 목록
    private CafeBusinessHoursDto cafeBusinessHours; // 요일별 영업시간 정보
    private List<CafeVibeTagDto> cafeVibeTags; // 카페에 해당하는 분위기 태그 목록
    private List<CafeReviewDto> cafeReviews; // 사용자 리뷰 목록

    /**
     * 카페 기본 정보 수신용 DTO
     */
    @Data
    @JsonNaming(PropertyNamingStrategies.SnakeCaseStrategy.class)
    public static class CafeInnerDto {
        private String cafeId; // 카페 식별자
        private String name; // 상호명
        private String thumbnailUrl; // 썸네일 이미지 key
        private String cafeIntro; // 카페 한 줄 소개 내용
    }

    /**
     * 카페 평점 및 통계 데이터 수신용 DTO
     */
    @Data
    @JsonNaming(PropertyNamingStrategies.SnakeCaseStrategy.class)
    public static class CafeRatingStatsDto {
        private Integer reviewCount; // 크롤링된 총 리뷰 수
        private Integer ratingSum; // 평점 총합 (추가)
        private String soloRatio; // 혼자 방문한 비율
        private String dateRatio; // 데이트 목적으로 방문한 비율
        private String friendsRatio; // 친구와 방문한 비율
    }

    /**
     * 카페 이미지 리스트 수신용 DTO
     */
    @Data
    @JsonNaming(PropertyNamingStrategies.SnakeCaseStrategy.class)
    public static class CafeImageDto {
        private String imageUrl; // 크롤링된 이미지 key
        private Integer sortOrder; // 이미지 정렬 순서
    }

    /**
     * 카페 메뉴 정보 리스트 수신용 DTO
     */
    @Data
    @JsonNaming(PropertyNamingStrategies.SnakeCaseStrategy.class)
    public static class CafeMenuDto {
        private String menuName; // 메뉴명 (ex. 아메리카노)
        private Integer price; // 메뉴 가격 (원 단위)
        private String menuDescription; // 메뉴에 대한 설명
    }

    /**
     * 요일별 영업시간 수신용 1:1 DTO
     */
    @Data
    @JsonNaming(PropertyNamingStrategies.SnakeCaseStrategy.class)
    public static class CafeBusinessHoursDto {
        private String monHours; // 월요일 영업시간 정보
        private String tuesHours; // 화요일 영업시간 정보
        private String wedHours; // 수요일 영업시간 정보
        private String thurHours; // 목요일 영업시간 정보 (오타 수정: thurs -> thur)
        private String friHours; // 금요일 영업시간 정보
        private String satHours; // 토요일 영업시간 정보
        private String sunHours; // 일요일 영업시간 정보
    }

    /**
     * 카페에 해당하는 분위기 태그 수신용 DTO
     */
    @Data
    @JsonNaming(PropertyNamingStrategies.SnakeCaseStrategy.class)
    public static class CafeVibeTagDto {
        private UUID tagId; // 기존 DB에 존재하는 분위기 태그 식별자 (UUID)
    }

    /**
     * 카페 사용자 리뷰 수신용 DTO
     */
    @Data
    @JsonNaming(PropertyNamingStrategies.SnakeCaseStrategy.class)
    public static class CafeReviewDto {
        private String userId; // 리뷰를 작성한 사용자 고유 식별자 (또는 이름)
        private String userReview; // 사용자가 남긴 텍스트 리뷰 내용
        private Short rating; // 사용자가 남긴 평점 (별점)
    }
}
