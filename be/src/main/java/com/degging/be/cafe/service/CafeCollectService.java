package com.degging.be.cafe.service;

import com.degging.be.cafe.client.CommercialStoreApiClient;
import com.degging.be.cafe.dto.response.external.StoreListInUpjongItem;
import com.degging.be.cafe.dto.response.external.StoreListInUpjongResponse;
import com.degging.be.cafe.repository.CafeRepository;
import com.degging.be.global.exception.BaseException;
import com.degging.be.global.exception.errorcode.CafeErrorCode;
import jakarta.transaction.Transactional;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;

import java.util.ArrayList;
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
    private final CafeDuplicateService cafeDuplicateService;
    private final CafeFranchiseService cafeFranchiseService;

    private static final List<String> UPJONG_CODES = List.of(
            "I21201", // 커피 전문점
            "I21202", // 제과점
            "I21203", // 아이스크림/빙수전문점
            "I21204"  // 기타 간이 식음료 점포 (도넛, 주스 등)
    );

    /**
     * 서울 내의 카페 및 디저트 업소 데이터 수집
     * 상가정보 API에서 업종별 데이터를 조회하여 DB에 저장
     */
    public void collectCafes() {
        int totalApiResultCount = 0; // 공공데이터 기준 전체 업소 수
        int totalSavedCount = 0;     // 최종 저장 성공 수
        int totalDuplicateCount = 0; // 중복(이미 DB에 있음) 수
        int totalNotFoundCount = 0;  // 카카오 매칭 실패 수
        int totalFilteredCount = 0;  // 지역/업종 필터링 제외 수

        for (String upjongCode : UPJONG_CODES) {
            log.info("업종 코드 [{}] 데이터 수집 시작", upjongCode);
            int pageNo = 1;
            int numOfRows = 1000;
            int currentUpjongTotal = 0;

            do {
                StoreListInUpjongResponse response = commercialStoreApiClient.fetchCafeStores(upjongCode, pageNo, numOfRows);

                if (response == null || response.getBody() == null) {
                    throw new BaseException(CafeErrorCode.EXTERNAL_API_ERROR);
                }

                if (response.getBody().getItems() == null) {
                    if (pageNo == 1) { // 첫 페이지부터 데이터가 없는 경우
                        log.warn("업종 코드 [{}]에 해당하는 데이터가 없습니다.", upjongCode);
                    }
                    break;
                }

                // 첫 페이지에서 해당 업종의 전체 개수 누적
                if (pageNo == 1) {
                    currentUpjongTotal = response.getBody().getTotalCount();
                    totalApiResultCount += currentUpjongTotal;
                }

                List<StoreListInUpjongItem> items = response.getBody().getItems();
                List<StoreListInUpjongItem> validCandidates = new ArrayList<>();

                for (StoreListInUpjongItem item : items) {

                    // 1. 서울 데이터만 저장
                    if (!isTargetRegion(item)) {
                        totalFilteredCount++;
                        continue;
                    }

                    // 2. 실제 카페만 저장 (필터링 로격 통과 시에만)
                    if (!cafeFilterService.isCafe(item)) {
                        totalFilteredCount++;
                        continue;
                    }

                    // 3. 좌표가 없으면 저장하지 않음
                    if (item.getLon() == null || item.getLat() == null) {
                        totalFilteredCount++;
                        continue;
                    }

                    // 4. 상가업소번호 기준 중복 저장 방지
                    if (cafeRepository.existsByBizesId(item.getBizesId())) {
                        totalDuplicateCount++;
                        continue;
                    }

                    validCandidates.add(item);
                }

                // 카카오 매칭 및 저장
                int savedInPage = cafeDuplicateService.matchKakaoPlaces(validCandidates);
                totalSavedCount += savedInPage;
                
                // 매칭 실패 수 계산 (전체 후보 - 실제 저장된 수)
                totalNotFoundCount += (validCandidates.size() - savedInPage);

                log.info("업종 [{}], 페이지 {} 완료. (누적 저장: {})", upjongCode, pageNo, totalSavedCount);
                pageNo++;

            } while ((pageNo - 1) * numOfRows < currentUpjongTotal);
        }

        log.info("========================================");
        log.info("서울 카페 데이터 수집 통합 결과");
        log.info("- 공공데이터 총 검색 결과: {}건", totalApiResultCount);
        log.info("- 필터링 제외(지역/비카페): {}건", totalFilteredCount);
        log.info("- 중복 스킵(DB 이미 존재): {}건", totalDuplicateCount);
        log.info("- 카카오 매칭 실패: {}건", totalNotFoundCount);
        log.info("- 최종 신규 저장 성공: {}건", totalSavedCount);
        log.info("========================================");

        // 수집 완료 후 프랜차이즈 여부 일괄 업데이트
        log.info("프랜차이즈 식별(업데이트) 로직 실행");
        cafeFranchiseService.updateFranchiseStatus();
    }

    // 서울특별시 데이터인지 확인
    private boolean isTargetRegion(StoreListInUpjongItem item) {
        return TARGET_REGION.equals(item.getCtprvnNm());
    }

}