package com.degging.be.cafe.service;

import com.degging.be.cafe.dto.request.CafeMapRequest;
import com.degging.be.cafe.dto.response.internal.CafeDetailResponse;
import com.degging.be.cafe.dto.response.internal.CafeMapResponse;
import com.degging.be.cafe.dto.response.internal.CafeOnboardingResponse;
import com.degging.be.cafe.entity.CafeEntity;
import com.degging.be.cafe.entity.CafeStatus;
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

import java.util.Collections;
import java.util.List;
import java.util.UUID;
import java.util.stream.Collectors;

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

    /**
     * 사용자 현재 위치를 기준으로 반경 2km 내의 카페 마커 목록을 조회합니다.
     *
     * @param request 사용자의 현재 위도(latitude)와 경도(longitude)를 담은 요청 객체
     * @return 조회된 카페들의 마커 정보(ID, 위도, 경도) 리스트
     */
    public List<CafeMapResponse> getCafeMarkers(CafeMapRequest request) {

        // 위/경도 좌표를 PostGIS POINT(경도 위도) 포맷 문자열로 변환
        String point = String.format("POINT(%f %f)", request.getLongitude(), request.getLatitude());

        // 고정된 반경 2,000미터(2km) 설정
        double radiusInMeters = 2000.0;

        // 레포지토리 호출해 리스트 가져오기
        List<CafeEntity> cafes = cafeRepository.findMarkersByRadius(point, radiusInMeters);

        // 정적 팩토리 메서드를 활용하여 DTO로 변환 후 반환
        return cafes.stream()
                .map(CafeMapResponse::from)
                .collect(Collectors.toList());
    }

    /**
     * 온보딩 화면에 표시할 랜덤 카페 리스트 조회
     *
     * @param count 추출할 카페 개수
     * @return 무작위로 추출된 카페 온보딩 응답 DTO 리스트
     */
    @Transactional(readOnly = true)
    public List<CafeOnboardingResponse> getRandomOnboardingItems(int count) {

        // 썸네일이 있고 영업 중인 카페 100개 조회
        List<CafeEntity> cafes = cafeRepository.findTop100ByThumbnailUrlIsNotNullAndStatus(CafeStatus.OPEN);

        // 리스트 랜덤 섞기
        Collections.shuffle(cafes);

        // 요청된 개수만큼 추출하여 DTO로 변환 후 반환
        return cafes.stream()
                .limit(count)
                .map(cafe -> CafeOnboardingResponse.builder()
                        .cafeId(cafe.getCafeId())
                        .thumbnailUrl(cafe.getThumbnailUrl())
                        .build())
                .toList();
    }

}