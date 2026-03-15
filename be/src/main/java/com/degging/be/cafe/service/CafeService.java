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

        // 가공된 데이터와 엔티티를 DTO 정적 팩토리 메서드에 전달
        return CafeDetailResponse.of(cafe, averageRating, totalReviews);
    }
}