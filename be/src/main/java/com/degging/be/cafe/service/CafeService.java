package com.degging.be.cafe.service;

import com.degging.be.cafe.dto.response.internal.CafeDetailResponse;
import com.degging.be.cafe.dto.response.internal.MenuResponse;
import com.degging.be.cafe.entity.CafeEntity;
import com.degging.be.cafe.entity.CafeImageEntity;
import com.degging.be.cafe.repository.CafeRepository;
import com.degging.be.global.exception.BaseException;
import com.degging.be.global.exception.errorcode.CafeErrorCode;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.util.List;
import java.util.UUID;
import java.util.stream.Collectors;

@Service
@RequiredArgsConstructor
@Transactional(readOnly = true)
public class CafeService {

    private final CafeRepository cafeRepository;

    /**
     * 카페 상세 정보 조회
     */
    public CafeDetailResponse getCafeDetail(UUID cafeId) {
        // 카페 존재 확인
        CafeEntity cafe = cafeRepository.findByIdWithDetail(cafeId)
                .orElseThrow(() -> new BaseException(CafeErrorCode.CAFE_NOT_FOUND));

        // 평균 평점 계산 (rating_sum / review_count)
        double averageRating = 0.0;
        int totalReviews = 0;

        if (cafe.getRatingStats() != null) {
            totalReviews = cafe.getRatingStats().getReviewCount();
            if (totalReviews > 0) {
                averageRating = (double) cafe.getRatingStats().getRatingSum() / totalReviews;
                averageRating = Math.round(averageRating * 10) / 10.0; // 소수점 첫째자리 반올림
            }
        }

        // 메뉴 엔티티 리스트 -> MenuResponse 리스트 변환
        List<MenuResponse> menus = cafe.getMenus().stream()
                .map(menu -> MenuResponse.builder()
                        .menuId(menu.getMenuId())
                        .menuName(menu.getMenuName())
                        .price(menu.getPrice())
                        .menuDescription(menu.getMenuDescription())
                        .build())
                .collect(Collectors.toList());

        // 이미지 엔티티 리스트 -> URL 문자열 리스트 변환
        List<String> images = cafe.getImages().stream()
                .map(CafeImageEntity::getImageUrl)
                .collect(Collectors.toList());

        // 분위기 태그 매핑 엔티티 -> 태그 이름 문자열 리스트 변환
        List<String> vibeTags = cafe.getVibeTags().stream()
                .map(vt -> vt.getVibe().getTagName())
                .collect(Collectors.toList());

        // 최종 Response 조립
        return CafeDetailResponse.builder()
                .cafeId(cafe.getCafeId())
                .name(cafe.getName())
                .cafeIntro(cafe.getCafeIntro())
                .rating(averageRating)
                .reviewCount(totalReviews)
                .status(cafe.getStatus().toString())
                .businessHours(cafe.getBusinessHours())
                .roadAddress(cafe.getRoadAddress())
                .phone(cafe.getPhone())
                .vibeTags(vibeTags)
                .images(images)
                .menus(menus)
                .build();
    }
}