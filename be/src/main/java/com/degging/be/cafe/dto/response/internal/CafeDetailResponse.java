package com.degging.be.cafe.dto.response.internal;

import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Getter;
import lombok.NoArgsConstructor;

import java.util.List;
import java.util.UUID;

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

    private String businessHours;   // 영업 시간

    private String roadAddress;     // 도로명 주소

    private String phone;   // 전화번호

    private List<String> vibeTags;      // vibe_entities 조인 결과

    private List<String> images;        // cafe_images: image_url 리스트

    private List<MenuResponse> menus;   // cafe_menus 리스트

}