package com.degging.be.review.dto.response;

import com.degging.be.review.entity.ReviewEntity;
import com.degging.be.review.entity.ReviewImageEntity;
import jakarta.validation.constraints.NotBlank;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Getter;
import lombok.NoArgsConstructor;

import java.time.LocalDateTime;
import java.util.List;
import java.util.UUID;

/**
 * 특정 리뷰 상세 정보 조회에 사용하는 응답 DTO
 */
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
        // 이미지가 null 일 경우 빈 리스트를 할당
        List<ReviewImageEntity> images = entity.getReviewImages() != null ?
                entity.getReviewImages() : List.of();

        return ReviewDetailResponse.builder()
                .reviewId(entity.getReviewId())
                .rating(entity.getRating())
                .content(entity.getContent())
                .createdAt(entity.getCreatedAt())
                .updatedAt(entity.getUpdatedAt())
                .imageUrls(images.stream()
                        .map(ReviewImageEntity::getImageUrl)
                        .toList())
                .nickname(entity.getUser().getNickname())
                // TODO: Cafe 도메인 연결 시 아래 주석 해제
                // .name(entity.getCafe().getName())
                // .cafeIntro(entity.getCafe().getCafeIntro())
                // .address(entity.getCafe().getAddress())
                // .roadAddress(entity.getCafe().getRoadAddress())
                .build();
    }
}
