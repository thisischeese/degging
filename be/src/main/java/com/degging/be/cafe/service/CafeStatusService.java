package com.degging.be.cafe.service;

import com.degging.be.cafe.client.SeoulFoodApiClient;
import com.degging.be.cafe.dto.response.external.SeoulFoodItem;
import com.degging.be.cafe.dto.response.external.SeoulFoodResponse;
import com.degging.be.cafe.entity.CafeEntity;
import com.degging.be.cafe.entity.CafeStatus;
import com.degging.be.cafe.repository.CafeRepository;
import com.degging.be.global.exception.BaseException;
import com.degging.be.global.exception.errorcode.CafeErrorCode;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.util.List;

/**
 * 서울시 인허가 데이터를 기반으로 카페의 영업 상태를 동기화하는 서비스
 */
@Slf4j
@Service
@RequiredArgsConstructor
public class CafeStatusService {

    private final SeoulFoodApiClient seoulFoodApiClient;
    private final CafeRepository cafeRepository;
    private final CafeDuplicateService cafeDuplicateService; // 주소 매칭 로직 재사용

    private static final int FETCH_SIZE = 1000;

    /**
     * 휴게음식점 인허가 데이터를 순회하며 카페 상태 동기화
     */
    public void syncAllCafeStatus() {
        int start = 1;
        int end = FETCH_SIZE;
        int totalUpdated = 0;

        while (true) {
            SeoulFoodResponse response = seoulFoodApiClient.fetchCafeStatus(start, end);

            if (response == null || response.getContent() == null) {
                log.error("서울시 인허가 API 호출 실패: {}", CafeErrorCode.EXTERNAL_API_ERROR.getMessage());
                throw new BaseException(CafeErrorCode.EXTERNAL_API_ERROR);
            }

            List<SeoulFoodItem> items = response.getContent().getRow();

            if (response.getContent().getRow() == null) {
                break;
            }

            // 페이지 단위로 트랜잭션을 분리하여 처리 (안정성 강화)
            totalUpdated += processSyncPage(items);

            // 전체 개수에 도달하면 종료
            if (end >= response.getContent().getListTotalCount()) {
                break;
            }

            start += FETCH_SIZE;
            end += FETCH_SIZE;
        }

        log.info("카페 영업 상태 동기화 완료. 총 업데이트된 카페 수: {}", totalUpdated);
    }

    /**
     * 페이지 단위로 업소 데이터를 매칭하고 영업 상태 업데이트
     * 
     * @param items API로부터 조회된 업소 리스트
     * @return 업데이트에 성공한 카페 수
     */
    @Transactional
    public int processSyncPage(List<SeoulFoodItem> items) {
        int updatedInPage = 0;
        for (SeoulFoodItem item : items) {
            if (updateStatusIfMatched(item)) {
                updatedInPage++;
            }
        }
        return updatedInPage;
    }

    /**
     * 인허가 카페 정보 하나를 기존 DB와 매칭하여 상태 업데이트
     *
     * @param item 매칭할 카페
     */
    private boolean updateStatusIfMatched(SeoulFoodItem item) {
        // 이름으로 먼저 후보군 조회
        List<CafeEntity> candidates = cafeRepository.findAllByName(item.getBplcNm());

        for (CafeEntity cafe : candidates) {
            // 기존에 구현한 주소 매칭 로직 활용
            if (cafeDuplicateService.isAddressMatch(cafe.getRoadAddress(), item.getRdnWhlAddr()) ||
                    cafeDuplicateService.isAddressMatch(cafe.getAddress(), item.getSiteWhlAddr())) {

                // 상태 값 매핑 및 업데이트
                CafeStatus status = mapToCafeStatus(item.getTrdStateNm());
                cafe.updateStatus(status);
                return true;
            }
        }
        return false;
    }

    /**
     * 서울시 상세영업상태명을 CafeStatus Enum으로 변환
     */
    private CafeStatus mapToCafeStatus(String trdStateNm) {
        if (trdStateNm == null) return CafeStatus.UNKNOWN;
        if (trdStateNm.contains("영업")) return CafeStatus.OPEN;
        if (trdStateNm.contains("폐업")) return CafeStatus.CLOSED;
        return CafeStatus.UNKNOWN;
    }
}