package com.degging.be.review.dto.response;

import com.degging.be.review.entity.ReviewEntity;
import com.degging.be.review.entity.ReviewImageEntity;
import jakarta.validation.constraints.NotBlank;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.extern.slf4j.Slf4j;

import java.io.IOException;
import java.time.LocalDateTime;
import java.util.ArrayList;
import java.util.Collections;
import java.util.List;
import java.util.UUID;

/**
 * 특정 리뷰 상세 정보 조회에 사용하는 응답 DTO
 */
@Slf4j
@Getter
@AllArgsConstructor
@NoArgsConstructor
@Builder
public class ReviewDetailResponse {
    private UUID reviewId;
    private Short rating;
    private String content;
    private LocalDateTime createdAt;
    private LocalDateTime updatedAt;
    private List<String> imageUrls; // 사진 정보
    private String nickname;        // 작성자 닉네임

    // 카페 정보(상호명, 큐레이션 1줄, 위치)
    private String name; // 상호명
    private String cafeIntro; // 한 줄 소개
    private String address; // 주소
    private String roadAddress; // 도로명 주소

    // Entity -> DTO
    public static ReviewDetailResponse toDto(ReviewEntity entity){
        // 리뷰 이미지 엔티티 리스트를 먼저 가져옴
        List<ReviewImageEntity> reviewImages = entity.getReviewImages();
        List<String> imageUrls; // 초기화 없이 선언만

        // 리뷰 이미지가 아예 없거나 리스트가 빈 경우
        if (reviewImages != null && !reviewImages.isEmpty() && reviewImages.getFirst().getThumbnailImageUrl() != null) {
            // 카페 썸네일을 리스트에 담음 (Null 방어 로직 추가 권장)
            String cafeThumbnail = entity.getCafe().getThumbnailUrl();
            imageUrls = (cafeThumbnail != null) ? List.of(cafeThumbnail) : Collections.emptyList();
        }
        // 리뷰 이미지가 있는 경우
        else {
            String cafeThumbnail = entity.getCafe().getThumbnailUrl();
            // 카페 썸네일마저 없다면 빈 리스트 반환
            imageUrls = (cafeThumbnail != null) ? List.of(cafeThumbnail) : Collections.emptyList();
            log.info("[카페 썸네일 대체] reviewId = {}, url = {}", entity.getReviewId(), cafeThumbnail);
        }

        return ReviewDetailResponse.builder()
                .reviewId(entity.getReviewId())
                .rating(entity.getRating())
                .content(entity.getContent())
                .createdAt(entity.getCreatedAt())
                .updatedAt(entity.getUpdatedAt())
                .imageUrls(imageUrls)
                .nickname(entity.getUser().getProfile().getNickname())
                 .name(entity.getCafe().getName())
                 .cafeIntro(entity.getCafe().getCafeIntro())
                 .address(entity.getCafe().getAddress())
                 .roadAddress(entity.getCafe().getRoadAddress())
                .build();
    }
}
