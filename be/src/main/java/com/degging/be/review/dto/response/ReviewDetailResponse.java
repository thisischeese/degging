package com.degging.be.review.dto.response;

import com.degging.be.cafe.entity.CafeEntity;
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
import java.util.*;

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
    private String cafeThumbnailImage; // 카페 썸네일 이미지

    // Entity -> DTO
    public static ReviewDetailResponse toDto(ReviewEntity entity) {
        // 카페 객체 안전하게 확보
        CafeEntity cafe = entity.getCafe();
        String cafeThumbnail = (cafe != null) ? cafe.getThumbnailUrl() : null;

        // 리뷰 이미지 리스트 안전하게 처리 (Stream 활용)
        // 리뷰 이미지가 있으면 해당 이미지들을 가져오고, 없거나 비었으면 카페 썸네일을 리스트에 담음
        List<String> imageUrls = Optional.ofNullable(entity.getReviewImages())
                .filter(list -> !list.isEmpty())
                .map(list -> list.stream()
                        .map(ReviewImageEntity::getImageUrl)
                        .filter(Objects::nonNull)
                        .toList())
                .filter(list -> !list.isEmpty()) // 필터링 후에도 비어있지 않은지 확인
                .orElseGet(() -> (cafeThumbnail != null) ? List.of(cafeThumbnail) : Collections.emptyList());

        // 로그 기록 (이미지 대체 시)
        if (imageUrls.size() == 1 && imageUrls.getFirst().equals(cafeThumbnail)) {
            log.info("[이미지 대체] reviewId = {}, 카페 썸네일 사용", entity.getReviewId());
        }

        // 빌더 패턴으로 응답 객체 생성 (카페 정보 null 방어 포함)
        return ReviewDetailResponse.builder()
                .reviewId(entity.getReviewId())
                .rating(entity.getRating())
                .content(entity.getContent())
                .createdAt(entity.getCreatedAt())
                .updatedAt(entity.getUpdatedAt())
                .imageUrls(imageUrls)
                .nickname(entity.getUser() != null && entity.getUser().getProfile() != null
                        ? entity.getUser().getProfile().getNickname() : "알 수 없음")
                .name(cafe != null ? cafe.getName() : "정보 없음")
                .cafeIntro(cafe != null ? cafe.getCafeIntro() : null)
                .address(cafe != null ? cafe.getAddress() : null)
                .roadAddress(cafe != null ? cafe.getRoadAddress() : null)
                .cafeThumbnailImage(cafeThumbnail)
                .build();
    }
}
