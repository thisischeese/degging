package com.degging.be.review.dto.response;

import com.degging.be.review.entity.ReviewEntity;
import com.degging.be.review.entity.ReviewImageEntity;
import lombok.*;

import java.time.LocalDateTime;
import java.util.ArrayList;
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
    @Setter
    private List<ReviewImageInfo> images; // 사진 정보
    private String nickname;        // 작성자 닉네임

    @Getter
    @Builder
    @AllArgsConstructor
    @NoArgsConstructor
    public static class ReviewImageInfo { // 내부 클래스
        private UUID imageId; // 리뷰 수정 시 사진 삭제하려면 필요
        private String imageUrl;
    }

    public ReviewResponse(UUID reviewId, short rating, String content, LocalDateTime createdAt, LocalDateTime updatedAt, String nickname) {
        this.reviewId = reviewId;
        this.rating = rating;
        this.content = content;
        this.createdAt = createdAt;
        this.updatedAt = updatedAt;
        this.nickname = nickname;
        this.images = new ArrayList<>(); // 이미지는 서비스에서 추가
    }

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
                .images(images.stream()
                        .map(img -> ReviewImageInfo.builder()
                                .imageId(img.getImageId()) // ID 추출
                                .imageUrl(img.getImageUrl())    // URL 추출
                                .build())
                        .toList())
                .nickname(entity.getUser().getNickname())
                .build();
    }

    /**
     * 이미지 리스트를 DTO 형태로 변환하여 주입하는 메서드
     */
    public void updateImages(List<com.degging.be.review.entity.ReviewImageEntity> imageEntities) {
        if (imageEntities == null) return;

        this.images = imageEntities.stream()
                .map(img -> ReviewImageInfo.builder()
                        .imageId(img.getImageId())
                        .imageUrl(img.getImageUrl())
                        .build())
                .toList();
    }

}