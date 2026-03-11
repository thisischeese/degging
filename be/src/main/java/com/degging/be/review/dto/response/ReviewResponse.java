package com.degging.be.review.dto.response;

import com.degging.be.review.entity.ReviewEntity;
import com.degging.be.review.entity.ReviewImageEntity;
import lombok.*;

import java.time.LocalDateTime;
import java.util.List;
import java.util.UUID;

/**
 * 특정 카페의 리뷰 리스트 응답 DTO
 */
@Getter
@AllArgsConstructor
@NoArgsConstructor
@Builder
public class ReviewResponse {
    private UUID reviewId;
    private Short rating;
    private String content;
    private LocalDateTime createdAt;
    private LocalDateTime updatedAt;
    private List<String> imageUrls; // 사진 정보
    private String nickname;        // 작성자 닉네임

    // Entity -> DTO
    public static ReviewResponse toDto(ReviewEntity entity){
        // 이미지가 null 일 경우 빈 리스트를 할당
        List<ReviewImageEntity> images = entity.getReviewImages() != null ?
                entity.getReviewImages() : List.of();

        return ReviewResponse.builder()
                .reviewId(entity.getReviewId())
                .rating(entity.getRating())
                .content(entity.getContent())
                .createdAt(entity.getCreatedAt())
                .updatedAt(entity.getUpdatedAt())
                .imageUrls(images.stream()
                        .map(ReviewImageEntity::getImageUrl)
                        .toList())
                .nickname(entity.getUser().getNickname())
                .build();
    }
}