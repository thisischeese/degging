package com.degging.be.cafe.dto.response.internal;

import com.degging.be.cafe.entity.CafeEntity;
import com.degging.be.cafe.entity.CafeImageEntity;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Getter;
import lombok.NoArgsConstructor;

import java.util.List;
import java.util.UUID;
import java.util.stream.Collectors;

/**
 * 카페 상세 정보 조회에 사용하는 응답 DTO
 */
@Getter
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class CafeDetailResponse {

    private UUID cafeId;

    private String name;    // 카페 상호명

    private String cafeIntro;   // 카페 한줄 소개

    private double rating;      // cafe_rating_stats: rating_sum / review_count

    private int reviewCount;    // cafe_rating_stats: review_count

    private String status;      // 카페 영업 상태

    private String businessHours;   // 금일 영업 시간

    private String roadAddress;     // 도로명 주소

    private String phone;   // 전화번호

    private List<String> vibeTags;      // vibe_entities 조인 결과

    private List<String> images;        // cafe_images: image_url 리스트

    private List<MenuResponse> menus;   // cafe_menus 리스트

    private boolean isScrapped; // 현재 로그인한 사용자의 찜 여부

    private String scrapColor;  // 찜한 폴더의 색상

    /**
     * 카페 엔티티와 가공된 통계 데이터를 바탕으로 상세 응답 DTO 생성
     * @param entity    카페 엔티티
     * @param rating    계산된 평균 평점
     * @param reviewCount   총 리뷰 수
     * @return  조합된 카페 상세 정보 응답 DTO
     */
    public static CafeDetailResponse of(CafeEntity entity, double rating, int reviewCount, boolean isScrapped, String scrapColor, String businessHours) {
        return CafeDetailResponse.builder()
                .cafeId(entity.getCafeId())
                .name(entity.getName())
                .cafeIntro(entity.getCafeIntro())
                .rating(rating)
                .reviewCount(reviewCount)
                .status(entity.getStatus().toString())
                .businessHours(businessHours)
                .roadAddress(entity.getRoadAddress())
                .phone(entity.getPhone())

                // 분위기 태그 매핑 엔티티 -> 태그 이름 문자열 리스트 변환
                .vibeTags(entity.getVibeTags().stream()
                        .map(vt -> vt.getVibe().getTagName())
                        .collect(Collectors.toList()))

                // 이미지 엔티티 리스트 -> URL 문자열 리스트 변환
                .images(entity.getImages().stream()
                        .map(CafeImageEntity::getImageUrl)
                        .collect(Collectors.toList()))

                // 메뉴 엔티티 리스트 -> MenuResponse 리스트 변환
                .menus(entity.getMenus().stream()
                        .map(MenuResponse::from)
                        .collect(Collectors.toList()))

                .isScrapped(isScrapped)
                .scrapColor(scrapColor)
                .build();
    }

}