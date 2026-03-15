package com.degging.be.cafe.service;

import com.degging.be.cafe.dto.response.internal.CafeDetailResponse;
import com.degging.be.cafe.entity.CafeEntity;
import com.degging.be.cafe.repository.CafeRepository;
import com.degging.be.global.exception.BaseException;
import com.degging.be.global.exception.errorcode.CafeErrorCode;
import com.degging.be.global.exception.errorcode.UserErrorCode;
import com.degging.be.scrap.repository.ScrapRepository;
import com.degging.be.user.entity.User;
import com.degging.be.user.repository.UserRepository;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.util.UUID;

@Service
@RequiredArgsConstructor
@Transactional(readOnly = true)
public class CafeService {

    private final UserRepository userRepository;
    private final CafeRepository cafeRepository;
    private final ScrapRepository scrapRepository;

    /**
     * 카페 상세 정보 조회
     * @param cafeId 조회할 카페 UUID
     * @param userId 현재 로그인한 사용자 ID (비로그인 시 null)
     * @return 가공된 카페 상세 정보 DTO
     */
    public CafeDetailResponse getCafeDetail(UUID userId, UUID cafeId) {
        // 유저 정보 조회
        User user = userRepository.findById(userId)
                .orElseThrow(() -> new BaseException(UserErrorCode.USER_NOT_FOUND));

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

        // 사용자 찜 여부 확인
        boolean isScrapped = scrapRepository.existsByUserIdAndCafeId(userId, cafeId);

        // 스크랩 폴더 색상
        String scrapColor = scrapRepository.findScrapColorByUserIdAndCafeId(userId, cafeId);

        // 가공된 데이터와 엔티티를 DTO 정적 팩토리 메서드에 전달
        return CafeDetailResponse.of(cafe, averageRating, totalReviews, isScrapped, scrapColor);
    }
}