package com.degging.be.review.dto.response;

import com.degging.be.global.entity.BaseEntity;
import com.degging.be.review.entity.ReviewEntity;
import lombok.Builder;
import lombok.Getter;

import java.time.LocalDateTime;
import java.util.UUID;

/**
 * 내 리뷰 전체 조회 응답 DTO
 */
@Getter
@Builder
public class MyReviewResponse {
    private UUID reviewId;
    private Short rating;
    private String content;
    private String cafeName; // 카페명
    private String thumbnailImage; // 썸네일 1장
    private LocalDateTime createdAt;
    private LocalDateTime updatedAt;

    // entity -> dto
    public static MyReviewResponse from(ReviewEntity entity) {
        // 썸네일 존재 확인
        String thumbKey = (entity.getReviewImages() != null && !entity.getReviewImages().isEmpty())
                ? entity.getReviewImages().getFirst().getImageUrl() 
                : entity.getCafe().getThumbnailUrl();

        return MyReviewResponse.builder()
                .reviewId(entity.getReviewId())
                .rating(entity.getRating())
                .content(entity.getContent())
                .cafeName(entity.getCafe().getName())
                .thumbnailImage(thumbKey)
                .createdAt(entity.getCreatedAt())
                .updatedAt(entity.getUpdatedAt())
                .build();
    }
}