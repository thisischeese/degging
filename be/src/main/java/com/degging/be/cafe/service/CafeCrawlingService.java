package com.degging.be.cafe.service;

import com.degging.be.infra.ai.AiClient;
import com.degging.be.cafe.dto.request.AiCrawlerRequestDto;
import com.degging.be.cafe.dto.response.external.AiCrawlerItemResponse;
import com.degging.be.cafe.dto.response.external.AiCrawlerResponse;
import com.degging.be.cafe.entity.CafeEntity;
import com.degging.be.cafe.repository.CafeRepository;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.ObjectProvider;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.PageRequest;
import org.springframework.scheduling.annotation.Async;
import org.springframework.stereotype.Service;

import java.io.File;
import java.util.ArrayList;
import java.util.List;
import java.util.stream.Collectors;

/**
 * 카페 크롤링 데이터를 처리하고 대량 수집 프로세스를 관리하는 서비스
 */
@Slf4j
@Service
@RequiredArgsConstructor
public class CafeCrawlingService {

    private final CafeRepository cafeRepository;
    private final AiClient aiClient;
    private final CafeCrawlingUpdateService cafeCrawlingUpdateService;
    private final CrawlingBackupService crawlingBackupService;

    // 프록시를 통한 자기 자신 호출을 위한 지연 주입
    private final ObjectProvider<CafeCrawlingService> cafeCrawlingServiceProvider;

    private static final int BATCH_SIZE = 100;

    /**
     * 수집된 데이터를 DB에 저장 (배치 단위로 트랜잭션 처리)
     * 
     * @param dataList 저장할 데이터 목록
     * @return 저장을 시도했지만 실패한 데이터 목록
     */
    public List<AiCrawlerItemResponse> saveCrawlingData(List<AiCrawlerItemResponse> dataList) {
        log.info("크롤링된 카페: {}개, 업데이트 진행 중...", dataList.size());
        List<AiCrawlerItemResponse> failedItems = new ArrayList<>();

        int count = 0;
        for (AiCrawlerItemResponse dto : dataList) {
            try {
                // 개별 업데이트가 실패하더라도 전체 배치가 롤백되지 않도록 별도 서비스 호출
                cafeCrawlingUpdateService.updateSingleCafe(dto);
                count++;

                // 10건마다 진행 상황 로그 출력
                if (count % 10 == 0) {
                    log.info("저장 중... ({}/{})", count, dataList.size());
                }
            } catch (Exception e) {
                log.error("저장 실패 (cafeId: {}): {}",
                        (dto.getCafes() != null ? dto.getCafes().getCafeId() : "unknown"), e.getMessage());
                failedItems.add(dto);
            }
        }
        log.info("배치 저장 완료! (성공: {}/전체: {})", count, dataList.size());
        return failedItems;
    }

    /**
     * 전체 카페에 대한 AI 크롤링 실행 (비동기)
     * DB에서 썸네일이 없는 카페 목록을 배치 단위로 읽어와 AI 서버에 크롤링 요청
     */
    @Async
    public void crawling() {
        // [추가] 크롤링 시작 전 백업 폴더를 확인하여 누락된 데이터 자동 복구
        autoBackfillFromBackups();

        List<String> targetRegions = List.of("역삼동");
        log.info("지정 지역 크롤링 프로세스 시작: {}", targetRegions);

        // 자기 자신을 프록시를 통해 호출하기 위해 Provider에서 가져옴
        CafeCrawlingService self = cafeCrawlingServiceProvider.getIfAvailable();
        if (self == null) {
            log.error("CafeCrawlingService 빈을 찾을 수 없습니다.");
            return;
        }

        for (String region : targetRegions) {
            long totalToCrawl = cafeRepository.countByThumbnailUrlIsNullAndRegion(region);
            log.info("[{}] 지역 크롤링 시작 (대상: {}개, 배치 크기: {})", region, totalToCrawl, BATCH_SIZE);

            if (totalToCrawl == 0) {
                log.info("[{}] 지역에 수집할 카페가 없습니다.", region);
                continue;
            }

            // 전체 배치 수 계산
            int totalBatches = (int) Math.ceil((double) totalToCrawl / BATCH_SIZE);

            for (int i = 0; i < totalBatches; i++) {
                int currentBatchNum = i + 1;
                log.info("[{}] 배치 {}/{} 데이터 {}개 조회 중...", region, currentBatchNum, totalBatches, BATCH_SIZE);

                // 해당 지역의 잔여 대상 중 상위 BATCH_SIZE개 조회
                Page<CafeEntity> cafePage = cafeRepository.findAllByThumbnailUrlIsNullAndRegion(region,
                        PageRequest.of(0, BATCH_SIZE));
                List<CafeEntity> currentBatch = cafePage.getContent();

                if (currentBatch.isEmpty()) {
                    log.info("[{}] 더 이상 수집할 데이터 없음.", region);
                    break;
                }

                // AI 서버 요청용 DTO 변환
                List<AiCrawlerRequestDto> requestBatch = currentBatch.stream()
                        .map(AiCrawlerRequestDto::from)
                        .collect(Collectors.toList());

                try {
                    log.info("[{}] 배치 {}/{} AI 서버 요청 전송... ({}건)", region, currentBatchNum, totalBatches,
                            requestBatch.size());
                    AiCrawlerResponse response = aiClient.crawl(requestBatch);

                    if (response != null && response.getItems() != null && !response.getItems().isEmpty()) {
                        log.info("[{}] 배치 {}/{} {}건 수신 성공, DB 저장을 시작합니다.", region, currentBatchNum, totalBatches,
                                response.getItems().size());

                        // AI 응답 즉시 JSON 백업
                        crawlingBackupService.backup(response, 1, currentBatchNum);

                        // 프록시 객체(self)를 통해 트랜잭션 보장하며 저장
                        self.saveCrawlingData(response.getItems());

                        if (response.getMissingCafeIds() != null && !response.getMissingCafeIds().isEmpty()) {
                            List<CafeEntity> missingCafes = cafeRepository.findAllById(response.getMissingCafeIds());
                            List<String> missingCafeInfo = missingCafes.stream()
                                    .map(c -> c.getName() + "(" + c.getCafeId() + ")")
                                    .collect(Collectors.toList());
                            log.warn("[{}] 배치 {}/{} AI 크롤링 누락 대상 ({}건): {}",
                                    region, currentBatchNum, totalBatches, missingCafeInfo.size(), missingCafeInfo);
                        }
                    } else {
                        log.warn("[{}] 배치 {}/{} AI 서버 응답이 없거나 비어있습니다.", region, currentBatchNum, totalBatches);
                    }
                } catch (Exception e) {
                    log.error("[{}] 배치 {}/{} 크롤링 작업 중 예외 발생: {}", region, currentBatchNum, totalBatches,
                            e.getMessage());
                }

                // 배치 간 지연 시간 추가 (AI 서버 부하 방지용)
                try {
                    log.info("다음 배치를 위해 2초간 대기합니다...");
                    Thread.sleep(2000);
                } catch (InterruptedException e) {
                    Thread.currentThread().interrupt();
                    log.warn("대기 중 인터럽트 발생: {}", e.getMessage());
                    break;
                }
            }
        }

        log.info("모든 지역의 크롤링 작업이 종료되었습니다.");
    }

    /**
     * 백업 폴더의 모든 JSON 파일을 읽어 DB를 업데이트 (Backfill)
     * 처리가 완료된 파일은 success 폴더로 이동합니다.
     */
    public void autoBackfillFromBackups() {
        log.info("[복구] 백업 데이터를 이용한 자동 복구 프로세스 시작");

        File[] backupFiles = crawlingBackupService.loadAllBackupFiles();
        if (backupFiles == null || backupFiles.length == 0) {
            log.info("[복구] 처리할 백업 파일이 없습니다.");
            return;
        }

        log.info("[복구] 총 {}개의 백업 파일 발견", backupFiles.length);

        int fileCount = 0;
        for (File file : backupFiles) {
            fileCount++;
            try {
                log.info("[복구 {}/{}] 파일 처리 중: {}", fileCount, backupFiles.length, file.getName());

                AiCrawlerResponse response = crawlingBackupService.loadResponse(file);
                if (response != null && response.getItems() != null && !response.getItems().isEmpty()) {
                    // 기존 저장 로직 재사용 (트랜잭션 보장 위해 self 호출)
                    CafeCrawlingService self = cafeCrawlingServiceProvider.getIfAvailable();
                    if (self != null) {
                        List<AiCrawlerItemResponse> failedItems = self.saveCrawlingData(response.getItems());

                        if (failedItems.isEmpty()) {
                            // 100% 성공 시 아카이빙
                            crawlingBackupService.archiveBackupFile(file);
                        } else {
                            // 일부 실패 시, 실패한 항목들로 파일 갱신 (점차 줄여나감)
                            log.warn("[복구] 파일 내 {}건 저장 실패로 파일 내용을 갱신합니다: {}", failedItems.size(), file.getName());
                            response.setItems(failedItems);
                            response.setTotal(failedItems.size()); // 남은 개수 갱신
                            crawlingBackupService.updateBackupFile(file, response);
                        }
                    }
                } else {
                    log.warn("[복구] 파일 내용이 비어있어 아카이빙합니다: {}", file.getName());
                    crawlingBackupService.archiveBackupFile(file);
                }
            } catch (Exception e) {
                log.error("[복구] 파일 처리 중 오류 발생 ({}): {}", file.getName(), e.getMessage());
            }
        }
        log.info("[복구] 모든 백업 파일 처리 완료");
    }

    /**
     * 특정 지역 내 지정된 카페들에 대해 크롤링을 수행
     * 
     * @param region 조회 대상 지역
     * @param cafeNames 크롤링할 카페 이름 리스트
     */
    public void crawlSpecificCafes(String region, List<String> cafeNames) {
        log.info("[특정 크롤링] 지역: {}, 검색 대상: {}개 시작", region, cafeNames.size());

        // 해당 이름과 지역에 해당하는 카페들 조회
        List<CafeEntity> targetCafes = cafeRepository.findAllByNameInAndRegion(cafeNames, region);
        
        if (targetCafes.isEmpty()) {
            log.warn("[특정 크롤링] 해당 조건에 맞는 카페를 찾을 수 없습니다: {}, {}", region, cafeNames);
            return;
        }

        log.info("[특정 크롤링] DB에서 {}개의 매칭된 카페 발견", targetCafes.size());

        // 크롤링 서버 요청용 DTO 변환
        List<AiCrawlerRequestDto> requestBatch = targetCafes.stream()
                .map(AiCrawlerRequestDto::from)
                .collect(Collectors.toList());

        // 크롤링 서버 요청 및 저장
        try {
            log.info("[특정 크롤링] AI 서버 요청 전송... ({}건)", requestBatch.size());
            AiCrawlerResponse response = aiClient.crawl(requestBatch);

            if (response != null && response.getItems() != null && !response.getItems().isEmpty()) {
                log.info("[특정 크롤링] {}건 수신 성공, DB 저장을 시작합니다.", response.getItems().size());
                
                // 트랜잭션 보장을 위해 프록시 객체(self) 호출
                CafeCrawlingService self = cafeCrawlingServiceProvider.getIfAvailable();
                if (self != null) {
                    self.saveCrawlingData(response.getItems());
                }

                if (response.getMissingCafeIds() != null && !response.getMissingCafeIds().isEmpty()) {
                    List<CafeEntity> missingCafes = cafeRepository.findAllById(response.getMissingCafeIds());
                    List<String> missingCafeInfo = missingCafes.stream()
                            .map(c -> c.getName() + " (" + c.getCafeId() + ")")
                            .collect(Collectors.toList());
                    log.warn("[특정 크롤링] AI 크롤링 누락 대상 ({}건): {}", missingCafeInfo.size(), missingCafeInfo);
                }
            } else {
                log.warn("[특정 크롤링] AI 서버 응답이 없거나 비어있습니다.");
            }
        } catch (Exception e) {
            log.error("[특정 크롤링] 크롤링 작업 중 오류 발생: {}", e.getMessage());
        }

        log.info("[특정 크롤링] 모든 작업이 종료되었습니다.");
    }
}
