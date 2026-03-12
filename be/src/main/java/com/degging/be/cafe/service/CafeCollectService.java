package com.degging.be.cafe.service;

import com.degging.be.cafe.client.CommercialStoreApiClient;
import com.degging.be.cafe.dto.response.StoreListInUpjongItem;
import com.degging.be.cafe.dto.response.StoreListInUpjongResponse;
import com.degging.be.cafe.entity.CafeEntity;
import com.degging.be.cafe.entity.CafeStatus;
import com.degging.be.cafe.repository.CafeRepository;
import jakarta.transaction.Transactional;
import lombok.RequiredArgsConstructor;
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
    private final GeometryFactory geometryFactory =
            new GeometryFactory(new PrecisionModel(), 4326);

    /**
     * 상가정보 API에서 카페 데이터 조회하여 DB에 저장
     *
     * @param pageNo 현재 페이지 번호
     * @param numOfRows 페이지당 조회 건수
     * @return 저장된 카페 수
     */
    public int collectCafes(int pageNo, int numOfRows) {
        StoreListInUpjongResponse response =
                commercialStoreApiClient.fetchCafeStores(pageNo, numOfRows);

        if (response == null ||
                response.getBody() == null ||
                response.getBody().getItems() == null) {
            return 0;
        }

        List<StoreListInUpjongItem> items = response.getBody().getItems();
        int savedCount = 0;

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
            // TODO:
            // 상가업소번호(bizesId)를 임시로 kakaoPlaceId 컬럼에 저장
            // 이후 카카오 API 매칭 후 실제 kakaoPlaceId로 업데이트할 예정
            if (cafeRepository.existsByKakaoPlaceId(item.getBizesId())) {
                continue;
            }

            CafeEntity cafe = CafeEntity.builder()
                    // TODO:
                    // 상가업소번호(bizesId)를 임시로 저장
                    // 이후 카카오 API 연동 후 실제 kakaoPlaceId로 업데이트할 예정
                    .kakaoPlaceId(item.getBizesId())

                    .name(item.getBizesNm())
                    .address(nullIfBlank(item.getLnoAdr()))
                    .roadAddress(nullIfBlank(item.getRdnmAdr()))
                    .phone(null)
                    .kakaoMapUrl(null)
                    .thumbnailUrl(null)
                    .status(CafeStatus.UNKNOWN)
                    .location(createPoint(item.getLon(), item.getLat()))
                    .cafeIntro(null)
                    .businessHours(null)
                    .build();

            cafeRepository.save(cafe);
            savedCount++;
        }

        return savedCount;
    }

    // 서울특별시 데이터인지 확인
    private boolean isTargetRegion(StoreListInUpjongItem item) {
        return TARGET_REGION.equals(item.getCtprvnNm());
    }

    // 경도/위도를 Point로 변환
    private Point createPoint(Double longitude, Double latitude) {
        return geometryFactory.createPoint(new Coordinate(longitude, latitude));
    }

    // 공백 문자열은 null로 변환
    private String nullIfBlank(String value) {
        if (value == null || value.isBlank()) {
            return null;
        }
        return value;
    }
}