package com.degging.be.cafe.service;

import com.degging.be.infra.external.client.KakaoLocalApiClient;
import com.degging.be.infra.external.dto.response.KakaoPlaceItem;
import com.degging.be.infra.external.dto.response.KakaoPlaceResponse;
import com.degging.be.infra.external.dto.response.StoreListInUpjongItem;
import com.degging.be.cafe.entity.CafeCategory;
import com.degging.be.cafe.entity.CafeEntity;
import com.degging.be.cafe.repository.CafeRepository;
import com.degging.be.global.exception.errorcode.CafeErrorCode;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.locationtech.jts.geom.Coordinate;
import org.locationtech.jts.geom.GeometryFactory;
import org.locationtech.jts.geom.Point;
import org.locationtech.jts.geom.PrecisionModel;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.util.ArrayList;
import java.util.List;

/**
 * 카카오 API를 이용해 카페 중복 매칭 및 신규 저장 처리하는 서비스
 */
@Slf4j
@Service
@RequiredArgsConstructor
public class CafeDuplicateService {

    private static final int SEARCH_PAGE = 1;
    private static final int SEARCH_SIZE = 10; // 결과 후보를 조금 더 늘려 매칭 확률 향상
    private static final int SEARCH_RADIUS = 1000; // 반경 1km 이내 검색

    private final KakaoLocalApiClient kakaoLocalApiClient;
    private final CafeRepository cafeRepository;
    private final CafeFilterService cafeFilterService;

    // SRID 4326 기준 Point 생성용 GeometryFactory
    // 위도/경도를 PostGIS로 바꿀 때 사용
    private final GeometryFactory geometryFactory = new GeometryFactory(new PrecisionModel(), 4326);

    /**
     * 카카오 API 기반 카페 매칭 실행
     *
     * 상세 정보가 채워지지 않은 카페 대상으로 매칭 작업 수행
     * 전체 리스트를 순회하며 카카오 검색 결과와 대조하여 유효한 경우 정보 갱신
     * 배치 처리를 통해 DB 조회 및 저장 성능 최적화 적용
     */
    @Transactional
    public int matchKakaoPlaces(List<StoreListInUpjongItem> items) {
        if (items == null || items.isEmpty()) {
            return 0;
        }

        List<CafeEntity> candidatesToSave = new ArrayList<>();
        int notFoundCount = 0;

        for (StoreListInUpjongItem item : items) {
            try {
                // 상호명 정규화 (괄호, 주식회사 등 제거)
                String normalizedName = normalizeName(item.getBizesNm());

                // 카테고리 판별 (커피/제과/디저트)
                CafeCategory category = cafeFilterService.determineCategory(item);

                // 카카오 데이터와 매칭 시도 (좌표 기반 검색 활용)
                KakaoPlaceItem matchedPlace = findMatchedPlace(item, normalizedName);

                // 매칭된 곳이 없으면 다음 item으로 넘어감
                if (matchedPlace == null) {
                    notFoundCount++;
                    continue;
                }

                // 엔티티 생성 (DB 저장은 나중에 일괄 처리)
                Point location = createPoint(item.getLon(), item.getLat());
                candidatesToSave.add(CafeEntity.of(item, matchedPlace, location, category));

            } catch (Exception e) {
                log.error("카페 매칭 처리 중 오류 발생 - 카페명: {}, 사유: {}", item.getBizesNm(), e.getMessage());
            }
        }

        if (candidatesToSave.isEmpty()) {
            log.info("카카오 매칭 작업 완료 - 매칭성공: 0, 미발견: {}", notFoundCount);
            return 0;
        }

        // --- 배치 최적화 시작: 중복 체크 및 최종 저장 (100건 단위로 쪼개서 처리) ---
        
        int totalSavedCount = 0;
        int totalDuplicateSkippedCount = 0;

        int batchSize = 100; // 한 번에 처리할 단위 (리스크 분산을 위해 100건으로 설정)
        for (int i = 0; i < candidatesToSave.size(); i += batchSize) {
            int end = Math.min(i + batchSize, candidatesToSave.size());
            List<CafeEntity> batchList = candidatesToSave.subList(i, end);

            // 현재 배치의 카카오 플레이스 ID 추출
            List<String> kakaoPlaceIds = batchList.stream()
                    .map(CafeEntity::getKakaoPlaceId)
                    .toList();

            try {
                // 이미 DB에 존재하는 카카오 플레이스 ID 리스트 조회 (배치 단위 쿼리)
                List<String> existingIds = cafeRepository.findAllExistingKakaoPlaceIds(kakaoPlaceIds);

                // 존재하지 않는 신규 카페만 필터링하여 저장 목록 확정
                List<CafeEntity> finalToSave = batchList.stream()
                        .filter(cafe -> !existingIds.contains(cafe.getKakaoPlaceId()))
                        .toList();

                // 최종 리스트 일괄 저장 (Batch Insert 효과로 성능 향상)
                if (!finalToSave.isEmpty()) {
                    cafeRepository.saveAll(finalToSave);
                    totalSavedCount += finalToSave.size();
                }
                
                // 중복 스킵된 수 누적
                totalDuplicateSkippedCount += (batchList.size() - finalToSave.size());

            } catch (Exception e) {
                log.error("배치 저장 중 오류 발생 - 범위: [{}~{}], 사유: {}", i, end, e.getMessage());
                // 해당 100건 실패 시 로그를 남기고 다음 100건으로 진행
            }
        }

        log.info("카카오 매칭 작업 완료 - 매칭성공: {}, 중복스킵: {}, 미발견: {}",
                totalSavedCount, totalDuplicateSkippedCount, notFoundCount);

        return totalSavedCount; // 실제 신규 저장된 수만 반환
    }

    /**
     * 카카오 API 직접 검색 및 저장
     * 공공데이터에 없는 카페를 이름으로 검색하여 저장할 때 사용
     *
     * @param name 검색할 카페 이름
     * @return 저장된 카페 수
     */
    @Transactional
    public int saveByKeyword(String keyword) {
        log.info("카카오 API 키워드 검색 및 저장 시작 - 검색어: {}", keyword);
        
        // 검색 수행 (위치 제한 없이 키워드 기반 검색)
        KakaoPlaceResponse response = kakaoLocalApiClient.searchPlaces(keyword, null, null, null, 1, 15);
        
        if (response == null || response.getDocuments() == null || response.getDocuments().isEmpty()) {
            log.warn("검색 결과가 없습니다 - 검색어: {}", keyword);
            return 0;
        }
        
        int savedCount = 0;
        for (KakaoPlaceItem item : response.getDocuments()) {
            // 1. 카페 카테고리인지 확인
            if (!isCafeCategory(item)) {
                continue;
            }
            
            // 2. 이미 존재하는지 확인 (KakaoPlaceId 기준)
            if (cafeRepository.existsByKakaoPlaceId(item.getId())) {
                log.info("이미 존재하는 카페 스킵: {} (ID: {})", item.getPlaceName(), item.getId());
                continue;
            }
            
            // 3. 엔티티 생성 및 저장
            try {
                Double lon = Double.parseDouble(item.getX());
                Double lat = Double.parseDouble(item.getY());
                Point location = createPoint(lon, lat);
                CafeCategory category = cafeFilterService.determineCategory(item);
                
                CafeEntity cafe = CafeEntity.of(item, location, category);
                cafeRepository.save(cafe);
                savedCount++;
                log.info("카페 추가 성공: {} (ID: {})", item.getPlaceName(), item.getId());
            } catch (Exception e) {
                log.error("카페 저장 중 오류 발생: {}, 사유: {}", item.getPlaceName(), e.getMessage());
            }
        }
        
        return savedCount;
    }

    /**
     * 상호명에서 검색에 불필요한 노이즈 제거
     */
    private String normalizeName(String name) {
        if (name == null) return "";
        return name.replaceAll("\\(주\\)", "")
                   .replaceAll("주식회사", "")
                   .replaceAll("\\(유\\)", "")
                   .replaceAll("\\(복\\)", "")
                   .replaceAll("\\(합\\)", "")
                   .trim();
    }

    /**
     * 특정 카페의 카카오 정보 업데이트 처리
     *
     * 동일한 카카오 플레이스 ID가 이미 존재하는지 검증하여 중복 저장 방지
     * 배치 처리가 아닌 단건 업데이트가 필요한 경우를 위해 유지
     */
    @Transactional
    public boolean processSave(StoreListInUpjongItem item, KakaoPlaceItem matchedPlace, Point location, CafeCategory category) {
        if (cafeRepository.existsByKakaoPlaceId(matchedPlace.getId())) {
            return false;
        }
        cafeRepository.save(CafeEntity.of(item, matchedPlace, location, category));
        return true;
    }

    /**
     * 카카오 검색 결과에서 동일 매장 찾기
     *
     * 카페 이름을 키워드로 검색하여 반환된 목록 중 주소가 가장 유사한 항목 선정
     * 좌표(x, y)와 반경(radius)을 활용해 검색 정확도 극대화
     *
     * @param item  매칭할 카페
     * @param keyword 정제된 검색 키워드
     */
    private KakaoPlaceItem findMatchedPlace(StoreListInUpjongItem item, String keyword) {
        // 좌표 기반 검색 수행
        KakaoPlaceResponse response = kakaoLocalApiClient.searchPlaces(
                keyword, 
                item.getLon(), 
                item.getLat(), 
                SEARCH_RADIUS, 
                SEARCH_PAGE, 
                SEARCH_SIZE
        );

        // 검색 결과 자체가 없는 경우
        if (response == null || response.getDocuments() == null || response.getDocuments().isEmpty()) {
            log.warn("매칭 실패 [{}]: 검색 결과 없음 - 카페명: [{}], 키워드: [{}]", 
                    CafeErrorCode.KAKAO_PLACE_NOT_FOUND.getCode(), item.getBizesNm(), keyword);
            return null;
        }

        // 검색 결과는 있으나 주소 또는 카테고리가 일치하는 항목이 없는 경우
        for (KakaoPlaceItem document : response.getDocuments()) {
            // 1. 주소 매칭 확인
            boolean addressMatched = isAddressMatch(item.getRdnmAdr(), document.getRoadAddressName()) ||
                    isAddressMatch(item.getLnoAdr(), document.getAddressName());

            if (addressMatched) {
                // 2. 카테고리 매칭 확인 (카페, 제과, 디저트 계열인지 검증)
                if (isCafeCategory(document)) {
                    return document;
                } else {
                    log.warn("매칭 무시: 주소는 일치하나 카테고리가 부적절함 - 카페명: [{}], 카테고리: [{}]", 
                             item.getBizesNm(), document.getCategoryName());
                }
            }
        }

        log.warn("매칭 실패 [{}]: 일치하는 결과 없음 - 카페명: [{}], 카카오 검색결과 {}건 중 유효항목 없음", 
                CafeErrorCode.KAKAO_PLACE_NOT_FOUND.getCode(), item.getBizesNm(), response.getDocuments().size());
        return null;
    }

    /**
     * 카카오 카테고리 정보가 카페 계열인지 확인
     */
    private boolean isCafeCategory(KakaoPlaceItem document) {
        String category = document.getCategoryName();
        String groupCode = document.getCategoryGroupCode();

        // 1. 카카오 카테고리 그룹 코드가 'CE7(카페)'인 경우
        if ("CE7".equals(groupCode)) {
            return true;
        }

        // 2. 카테고리 경로명에 카페, 커피, 제과, 베이커리, 디저트 등이 포함된 경우
        if (category != null) {
            boolean isCafePath = category.contains("카페") || 
                                 category.contains("커피") || 
                                 category.contains("제과") || 
                                 category.contains("베이커리") || 
                                 category.contains("디저트") || 
                                 category.contains("아이스크림") || 
                                 category.contains("도넛");

            // 술집, 포차, 이자카야 등은 카페 키워드가 있어도 제외 (ex. 술집 > 이색카페 등 방지)
            boolean isExcludedPath = category.contains("술집") || 
                                     category.contains("호프") || 
                                     category.contains("포차") || 
                                     category.contains("이자카야") || 
                                     category.contains("주점");

            return isCafePath && !isExcludedPath;
        }

        return false;
    }

    /**
     * 주소 문자열 비교 및 유효성 검사
     *
     * 입력된 두 주소에서 공백을 모두 제거한 후 포함 관계 확인
     * 행정 구역 표기 차이로 인한 매칭 실패를 최소화하기 위해 유연한 비교 방식 사용
     *
     * @param source    db에 저장되어 있던 카페
     * @param target    카카오 API로 검색한 카페
     */
    public boolean isAddressMatch(String source, String target) {
        if (source == null || target == null) {
            return false;
        }

        // 서울특별시, 서울, 공백을 모두 제거하여 순수 주소 정보만 남김
        String cleanSource = source.replace("서울특별시", "").replace("서울", "").replaceAll("\\s+", "");
        String cleanTarget = target.replace("서울특별시", "").replace("서울", "").replaceAll("\\s+", "");

        // 정제된 주소가 서로를 포함하고 있는지 확인
        return cleanSource.contains(cleanTarget) || cleanTarget.contains(cleanSource);
    }

    /**
     * 경도/위도를 Point로 변환
     *
     * @param longitude 경도
     * @param latitude 위도
     * @return Point로 변환된 값
     */
    private Point createPoint(Double longitude, Double latitude) {
        return geometryFactory.createPoint(new Coordinate(longitude, latitude));
    }
}