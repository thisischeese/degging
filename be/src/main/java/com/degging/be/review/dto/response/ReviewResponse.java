package com.degging.be.review.dto.response;

import com.degging.be.cafe.entity.CafeEntity;
import com.degging.be.review.entity.ReviewEntity;
import com.degging.be.review.entity.ReviewImageEntity;
import lombok.*;
import lombok.extern.slf4j.Slf4j;

import java.time.LocalDateTime;
import java.util.ArrayList;
import java.util.Collections;
import java.util.List;
import java.util.UUID;

/**
 * 특정 카페의 리뷰 리스트 응답 DTO
 */
@Slf4j
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
        List<ReviewImageEntity> reviewImages = entity.getReviewImages();
        List<ReviewImageInfo> imageInfos;

        // 1. 리뷰 이미지가 존재하는 경우 처리
        if (reviewImages != null && !reviewImages.isEmpty()) {
            imageInfos = reviewImages.stream()
                    .map(img -> ReviewImageInfo.builder()
                            .imageId(img.getImageId())
                            .imageUrl(img.getImageUrl())
                            .build())
                    .toList();
        }
        // 2. 리뷰 이미지가 없는 경우 -> 카페 썸네일로 대체
        else {
            String cafeThumbnail = (entity.getCafe() != null) ? entity.getCafe().getThumbnailUrl() : null;

            imageInfos = (cafeThumbnail != null)
                    ? List.of(ReviewImageInfo.builder()
                    .imageId(null) // 대체 이미지이므로 ID는 null 혹은 0L
                    .imageUrl(cafeThumbnail)
                    .build())
                    : Collections.emptyList();
            if (cafeThumbnail != null){
                log.info("카페 썸네일이 없음 이슈");
            }

            log.info("[이미지 대체] reviewId = {}, 카페 썸네일 사용", entity.getReviewId());
        }

        return ReviewResponse.builder()
                .reviewId(entity.getReviewId())
                .rating(entity.getRating())
                .content(entity.getContent())
                .createdAt(entity.getCreatedAt())
                .updatedAt(entity.getUpdatedAt())
                .images(imageInfos) // 변환된 리스트 주입
                .nickname(entity.getUser() != null && entity.getUser().getProfile() != null
                        ? entity.getUser().getProfile().getNickname() : "알 수 없음")
                .build();
    }

    /**
     * 이미지 리스트를 DTO 형태로 변환하여 주입하는 메서드
     */
    public void updateImages(List<com.degging.be.review.entity.ReviewImageEntity> imageEntities, CafeEntity cafe) {
        // 1. 이미지가 존재하는 경우 변환하여 할당
        if (imageEntities != null && !imageEntities.isEmpty()) {
            this.images = imageEntities.stream()
                    .map(img -> ReviewImageInfo.builder()
                            .imageId(img.getImageId())
                            .imageUrl(img.getImageUrl())
                            .build())
                    .toList();
        }
        // 2. 이미지가 없는 경우 카페 썸네일을 기본 이미지로 할당
        else if (cafe != null && cafe.getThumbnailUrl() != null) {
            this.images = List.of(ReviewImageInfo.builder()
                    .imageId(null) // DB 엔티티가 아니므로 ID는 null 혹은 특정 상수
                    .imageUrl(cafe.getThumbnailUrl())
                    .build());
        }
        // 3. 둘 다 없는 경우 빈 리스트 (NPE 방지)
        else {
            this.images = Collections.emptyList();
        }
    }

}