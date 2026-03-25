package com.degging.be.cafe.service;

import com.degging.be.cafe.dto.request.CafeBottomSheetRequest;
import com.degging.be.cafe.dto.request.CafeBottomSheetSort;
import com.degging.be.cafe.dto.request.CafeMapRequest;
import com.degging.be.cafe.dto.response.internal.CafeBottomSheetResponse;
import com.degging.be.cafe.dto.response.internal.CafeDetailResponse;
import com.degging.be.cafe.dto.response.internal.CafeMapMarkersResponse;
import com.degging.be.cafe.dto.response.internal.CafeMapResponse;
import com.degging.be.cafe.dto.response.internal.CafeOnboardingResponse;
import com.degging.be.cafe.entity.CafeEntity;
import com.degging.be.cafe.entity.CafeStatus;
import com.degging.be.cafe.repository.CafeRepository;
import com.degging.be.global.exception.BaseException;
import com.degging.be.global.exception.errorcode.CafeErrorCode;
import com.degging.be.global.exception.errorcode.UserErrorCode;
import com.degging.be.global.exception.errorcode.CommonErrorCode;
import com.degging.be.scrap.repository.ScrapRepository;
import com.degging.be.user.entity.UserEntity;
import com.degging.be.user.repository.UserRepository;
import com.degging.be.user.service.MemberService;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import java.util.Map;
import java.util.HashMap;
import org.springframework.data.domain.PageRequest;
import org.springframework.data.domain.Slice;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.util.Collections;
import java.util.List;
import java.util.UUID;
import java.util.stream.Collectors;

@Slf4j
@Service
@RequiredArgsConstructor
@Transactional(readOnly = true)
public class CafeService {

    private final UserRepository userRepository;
    private final CafeRepository cafeRepository;
    private final ScrapRepository scrapRepository;
    private final MemberService memberService;

    /**
     * 카페 상세 정보 조회
     * @param cafeId 조회할 카페 UUID
     * @param userId 현재 로그인한 사용자 ID (비로그인 시 null)
     * @return 가공된 카페 상세 정보 DTO
     */
    public CafeDetailResponse getCafeDetail(UUID userId, UUID cafeId) {

        // 유저 정보 조회
        UserEntity user = userRepository.findById(userId)
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

        // 오늘 요일에 해당하는 영업시간 추출
        String businessHours = "영업 정보 없음";
        java.time.DayOfWeek today = java.time.LocalDate.now().getDayOfWeek();
        if (cafe.getBusinessHoursEntity() != null) {
            com.degging.be.cafe.entity.CafeBusinessHoursEntity hoursEntity = cafe.getBusinessHoursEntity();
            businessHours = switch (today) {
                case MONDAY -> hoursEntity.getMonHours();
                case TUESDAY -> hoursEntity.getTuesHours();
                case WEDNESDAY -> hoursEntity.getWedHours();
                case THURSDAY -> hoursEntity.getThurHours();
                case FRIDAY -> hoursEntity.getFriHours();
                case SATURDAY -> hoursEntity.getSatHours();
                case SUNDAY -> hoursEntity.getSunHours();
            };
            if (businessHours == null) {
                businessHours = "영업 정보 없음";
            }
        }

        // 가공된 데이터와 엔티티를 DTO 정적 팩토리 메서드에 전달
        return CafeDetailResponse.of(cafe, averageRating, totalReviews, isScrapped, scrapColor, businessHours);
    }

    /**
     * 사용자 현재 위치를 기준으로 반경 2km 내의 카페 마커 목록을 조회합니다.
     * 로그인한 사용자의 경우 선호 태그가 지정되지 않았다면 상위 3개 선호 태그로 자동 필터링합니다.
     *
     * @param userId  인증된 사용자 ID (nullable)
     * @param request 사용자의 현재 위도(latitude)와 경도(longitude) 및 태그 필터를 담은 요청 객체
     * @return 조회된 카페들의 마커 정보와 적용된 필터 태그 정보
     */
    public CafeMapMarkersResponse getCafeMarkers(UUID userId, CafeMapRequest request) {

        // 위/경도 좌표를 PostGIS POINT(경도 위도) 포맷 문자열로 변환
        String point = String.format("POINT(%f %f)", request.getLongitude(), request.getLatitude());

        // 고정된 반경 2,000미터(2km) 설정
        double radiusInMeters = 2000.0;

        // 태그 추출 (요청에 없으면 사용자 선호 태그 조회)
        List<String> tags = request.getTags();
        if ((tags == null || tags.isEmpty()) && userId != null) {
            tags = memberService.getUserPreferred(userId);
            request.setTags(tags);
        }

        // 레포지토리 호출해 리스트 가져오기 (태그 존재 여부에 따라 분기)
        List<CafeEntity> cafes;
        if (tags != null && !tags.isEmpty()) {
            cafes = cafeRepository.findMarkersByRadiusAndTags(point, radiusInMeters, request.isIncludeFranchise(), tags);
        } else {
            cafes = cafeRepository.findMarkersByRadius(point, radiusInMeters, request.isIncludeFranchise());
        }

        // 정적 팩토리 메서드를 활용하여 DTO로 변환
        List<CafeMapResponse> markers = cafes.stream()
                .map(CafeMapResponse::from)
                .collect(Collectors.toList());

        // 마커 정보와 사용된 필터 태그를 함께 반환
        return CafeMapMarkersResponse.of(markers, tags);
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
                .map(CafeOnboardingResponse::from)
                .toList();
    }

    /**
     * 지도 바텀시트용 카페 리스트 조회
     *
     * 반경 2km 내 카페를 프랜차이즈 필터 및 정렬 기준에 따라 반환
     * 무한 스크롤 지원을 위해 Slice 기반 처리
     *
     * @param request  위치 좌표, 프랜차이즈 포함 여부, 정렬 기준을 담은 요청 객체
     * @param page     페이지 번호 (0부터 시작)
     * @param size     페이지 당 카페 수
     * @return 바텀시트 카페 요약 정보
     */
    public Slice<CafeBottomSheetResponse> getBottomSheetCafes(UUID userId, CafeBottomSheetRequest request, int page, int size) {

        // PostGIS 쿼리에서 사용할 수 있도록 위경도를 "POINT(경도 위도)" 포맷의 문자열로 변환
        String point = String.format("POINT(%f %f)", request.getLongitude(), request.getLatitude());
        
        // 검색 반경 2000 미터(2km)
        double radiusInMeters = 2000.0;
        
        // 프랜차이즈 포함 여부
        boolean includeFranchise = request.isIncludeFranchise();
        
        // 페이징 데이터(page, size) 설정. 정렬은 쿼리 단에서 처리.
        PageRequest pageRequest = PageRequest.of(page, size);

        // 정렬 기준이 오지 않았을 경우, 기본 정렬 기준 '추천순(RECOMMEND)'으로 설정
        CafeBottomSheetSort sort = request.getSort() != null ? request.getSort() : CafeBottomSheetSort.RECOMMEND;

        // 태그 추출 (요청에 없으면 사용자 선호 태그 조회)
        List<String> tags = request.getTags();
        if ((tags == null || tags.isEmpty()) && userId != null) {
            tags = memberService.getUserPreferred(userId);
            request.setTags(tags);
        }

        // 정렬 기준별 Repository 메서드 분기 호출 (태그 존재 여부에 따라 분기)
        Slice<CafeEntity> cafes;
        if (tags != null && !tags.isEmpty()) {
            cafes = switch (sort) {
                case RATING -> cafeRepository.findBottomSheetByRatingAndTags(point, radiusInMeters, includeFranchise, tags, pageRequest);
                case REVIEW_COUNT -> cafeRepository.findBottomSheetByReviewCountAndTags(point, radiusInMeters, includeFranchise, tags, pageRequest);
                case DISTANCE -> cafeRepository.findBottomSheetByDistanceAndTags(point, radiusInMeters, includeFranchise, tags, pageRequest);
                default -> cafeRepository.findBottomSheetByDistanceAndTags(point, radiusInMeters, includeFranchise, tags, pageRequest);
            };
        } else {
            cafes = switch (sort) {
                case RATING -> cafeRepository.findBottomSheetByRating(point, radiusInMeters, includeFranchise, pageRequest);
                case REVIEW_COUNT -> cafeRepository.findBottomSheetByReviewCount(point, radiusInMeters, includeFranchise, pageRequest);
                case DISTANCE -> cafeRepository.findBottomSheetByDistance(point, radiusInMeters, includeFranchise, pageRequest);
                /* TODO: RECOMMEND(추천순)은 AI 연동 후 별도 로직으로 교체 예정. 현재는 기본 반환(거리순)으로 처리 */
                default -> cafeRepository.findBottomSheetByDistance(point, radiusInMeters, includeFranchise, pageRequest);
            };
        }

        return cafes.map(cafe -> {
            boolean isScrapped = false;
            if (userId != null) {
                isScrapped = scrapRepository.existsByUserIdAndCafeId(userId, cafe.getCafeId());
            }
            return CafeBottomSheetResponse.from(cafe, isScrapped);
        });
    }

    /**
     * 프론트엔드 검색 시작 - AI 처리 전 수신 확인용
     * @param request 프론트엔드가 보낸 원본 검색어 및 좌표
     * @return 임시 분석 결과
     */
    public Map<String, String> processSearch(com.degging.be.cafe.dto.request.CafeSearchRequest request) {
        log.info("검색 요청 수신됨! 키워드: {}, 좌표: ({}, {})",
                request.getKeyword(), request.getLatitude(), request.getLongitude());

        Map<String, String> dummyData = new HashMap<>();
        dummyData.put("originalKeyword", request.getKeyword());
        dummyData.put("status", "[더미] 정상 수신 완료 (AI 연동 대기)");
        
        return dummyData;
    }

}
