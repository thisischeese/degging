package com.degging.be.cafe.service;

import com.degging.be.cafe.client.CommercialStoreApiClient;
import com.degging.be.cafe.dto.response.StoreListInUpjongItem;
import com.degging.be.cafe.dto.response.StoreListInUpjongResponse;
import com.degging.be.cafe.entity.CafeEntity;
import com.degging.be.cafe.entity.CafeStatus;
import com.degging.be.cafe.repository.CafeRepository;
import jakarta.transaction.Transactional;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.locationtech.jts.geom.Coordinate;
import org.locationtech.jts.geom.GeometryFactory;
import org.locationtech.jts.geom.Point;
import org.locationtech.jts.geom.PrecisionModel;
import org.springframework.stereotype.Service;

import java.util.List;

/**
 * 상가정보 API를 통해 카페 데이터를 수집하고 저장하는 서비스
 *
 * 현재 흐름
 * 1. 소상공인시장진흥공단 상가정보 API 호출
 * 2. 서울 데이터만 필터링
 * 3. 실제 카페만 필터링
 * 4. 중복 체크
 * 5. CafeEntity 저장
 */
@Slf4j
@Service
@RequiredArgsConstructor
@Transactional
public class CafeCollectService {

    // MVP 단계에서는 서울 지역만 수집
    private static final String TARGET_REGION = "서울특별시";

    private final CommercialStoreApiClient commercialStoreApiClient;
    private final CafeFilterService cafeFilterService;
    private final CafeRepository cafeRepository;

    // SRID 4326 기준 Point 생성용 GeometryFactory
    // 위도/경도를 PostGIS로 바꿀 때 사용
    private final GeometryFactory geometryFactory = new GeometryFactory(new PrecisionModel(), 4326);

    /**
     * 서울 내의 카페 전체 데이터 수집
     * 상가정보 API에서 카페 데이터 조회하여 DB에 저장
     * return 없음. 데이터 수집 실행 후 로그로 결과 출력
     */
    public void collectCafes() {
        int pageNo = 1; // 현재 조회할 페이지 번호
        int numOfRows = 1000;   // 한번에 조회할 데이터 수
        int totalCount = 0; // 전체 데이터 개수
        int savedCount = 0; // 실제 DB에 저장된 카페 수

        // 최소 1번은 API를 호출해야 totalCount를 알 수 있기 때문에 do-while 사용
        do {
            // 현재 페이지의 카페 업소 목록 조회
            StoreListInUpjongResponse response =
                    commercialStoreApiClient.fetchCafeStores(pageNo, numOfRows);

            // 응답 자체가 없거나 업소 목록이 없으면 종료
            if (response == null || response.getBody() == null || response.getBody().getItems() == null) {
                log.warn("카페 데이터 수집 중 응답이 비정상적입니다. pageNo={}", pageNo);
                return;
            }

            // 전체 업소 개수 응답에서 가져옴
            totalCount = response.getBody().getTotalCount();

            // 현재 페이지에 있는 업소 목록
            List<StoreListInUpjongItem> items = response.getBody().getItems();

            for (StoreListInUpjongItem item : items) {

                // 서울 데이터만 저장
                if (!isTargetRegion(item)) {
                    continue;
                }

                // 실제 카페만 저장
                if (!cafeFilterService.isCafe(item)) {
                    continue;
                }

                // 좌표가 없으면 저장하지 않음
                if (item.getLon() == null || item.getLat() == null) {
                    continue;
                }

                // 상가업소번호 기준 중복 저장 방지
                if (cafeRepository.existsByKakaoPlaceId(item.getBizesId())) {
                    continue;
                }

                // 업소의 경도/위도를 Point 타입으로 변환
                Point location = createPoint(item.getLon(), item.getLat());

                // API 응답 데이터를 기반으로 저장할 카페 엔티티 생성
                CafeEntity cafe = CafeEntity.from(item, location);

                // DB에 저장
                cafeRepository.save(cafe);

                savedCount++;
            }
            pageNo++;
        } while ((pageNo - 1) * numOfRows < totalCount);

        log.info("서울 카페 데이터 수집 완료. 총 저장된 카페 수: {}", savedCount);
    }

    // 서울특별시 데이터인지 확인
    private boolean isTargetRegion(StoreListInUpjongItem item) {
        return TARGET_REGION.equals(item.getCtprvnNm());
    }

    // 경도/위도를 Point로 변환
    private Point createPoint(Double longitude, Double latitude) {
        return geometryFactory.createPoint(new Coordinate(longitude, latitude));
    }
}