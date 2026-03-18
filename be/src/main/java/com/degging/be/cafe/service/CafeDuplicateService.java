package com.degging.be.cafe.service;

import com.degging.be.cafe.client.KakaoLocalApiClient;
import com.degging.be.cafe.dto.response.external.KakaoPlaceItem;
import com.degging.be.cafe.dto.response.external.KakaoPlaceResponse;
import com.degging.be.cafe.dto.response.external.StoreListInUpjongItem;
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

import java.util.List;

/**
 * 카카오 API를 이용해 카페 중복 매칭 및 신규 저장 처리하는 서비스
 */
@Slf4j
@Service
@RequiredArgsConstructor
public class CafeDuplicateService {

    private static final int SEARCH_PAGE = 1;
    private static final int SEARCH_SIZE = 5;

    private final KakaoLocalApiClient kakaoLocalApiClient;
    private final CafeRepository cafeRepository;

    // SRID 4326 기준 Point 생성용 GeometryFactory
    // 위도/경도를 PostGIS로 바꿀 때 사용
    private final GeometryFactory geometryFactory = new GeometryFactory(new PrecisionModel(), 4326);

    /**
     * 카카오 API 기반 카페 매칭 실행
     *
     * 상세 정보가 채워지지 않은 카페 대상으로 매칭 작업 수행
     * 전체 리스트를 순회하며 카카오 검색 결과와 대조하여 유효한 경우 정보 갱신
     */
    public int matchKakaoPlaces(List<StoreListInUpjongItem> items) {
        int matchedCount = 0;
        int duplicateSkippedCount = 0;
        int notFoundCount = 0;

        for (StoreListInUpjongItem item : items) {
            try {
                // 카카오 데이터와 매칭 시도
                KakaoPlaceItem matchedPlace = findMatchedPlace(item);

                // 매칭된 곳이 없으면 다음 item으로 넘어감
                if (matchedPlace == null) {
                    notFoundCount++;
                    continue;
                }

                // 매칭 성공 시 저장 로직 호출
                Point location = createPoint(item.getLon(), item.getLat());
                if (processSave(item, matchedPlace, location)) {
                    matchedCount++;
                } else {
                    duplicateSkippedCount++;
                }

            } catch (Exception e) {
                log.error("카페 매칭 처리 중 오류 발생 - 카페ID: {}, 사유: {}", item.getBizesNm(), e.getMessage());
            }
        }

        log.info("카카오 매칭 작업 완료 - 매칭성공: {}, 중복스킵: {}, 미발견: {}",
                 matchedCount, duplicateSkippedCount, notFoundCount);

        return matchedCount;
    }

    /**
     * 특정 카페의 카카오 정보 업데이트 처리
     *
     * 동일한 카카오 플레이스 ID가 이미 존재하는지 검증하여 중복 저장 방지
     * 트랜잭션을 짧게 유지하기 위해 개별 업데이트 단위 처리
     *
     * @param item  저장할 카페 데이터
     * @param matchedPlace  일치한 카카오 API의 카페 정보
     */
    @Transactional
    public boolean processSave(StoreListInUpjongItem item, KakaoPlaceItem matchedPlace, Point location) {

        // 중복 방지
        if (cafeRepository.existsByKakaoPlaceId(matchedPlace.getId())) {
            return false;
        }

        // 엔티티 생성
        CafeEntity cafe = CafeEntity.of(item, matchedPlace, location);

        // DB 저장
        cafeRepository.save(cafe);

        return true;
    }

    /**
     * 카카오 검색 결과에서 동일 매장 찾기
     *
     * 카페 이름을 키워드로 검색하여 반환된 목록 중 주소가 가장 유사한 항목 선정
     * 도로명 주소와 지번 주소 모두를 대조
     *
     * @param item  매칭할 카페
     */
    private KakaoPlaceItem findMatchedPlace(StoreListInUpjongItem item) {
        KakaoPlaceResponse response = kakaoLocalApiClient.searchPlaces(item.getBizesNm(), SEARCH_PAGE, SEARCH_SIZE);

        // 카카오 API 검색 결과가 아예 없을 경우, 로그에 에러코드 명시
        if (response == null || response.getDocuments() == null || response.getDocuments().isEmpty()) {
            log.warn("매칭 실패 코드: {}, 대상: {}", CafeErrorCode.KAKAO_PLACE_NOT_FOUND.getCode(), item.getBizesNm());
            return null;
        }

        for (KakaoPlaceItem document : response.getDocuments()) {
            if (isAddressMatch(item.getRdnmAdr(), document.getRoadAddressName()) ||
                    isAddressMatch(item.getLnoAdr(), document.getAddressName())) {
                return document;
            }
        }

        return null;
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