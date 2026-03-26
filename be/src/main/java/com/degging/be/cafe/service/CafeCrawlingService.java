package com.degging.be.cafe.service;

import com.degging.be.cafe.client.AiCrawlerApiClient;
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
    private final AiCrawlerApiClient aiCrawlerApiClient;
    private final CafeCrawlingUpdateService cafeCrawlingUpdateService;
    private final CrawlingBackupService crawlingBackupService;

    // 프록시를 통한 자기 자신 호출을 위한 지연 주입
    private final ObjectProvider<CafeCrawlingService> cafeCrawlingServiceProvider;

    private static final int BATCH_SIZE = 50;

    /**
     * 수집된 데이터를 DB에 저장 (배치 단위로 트랜잭션 처리)
     */
    public void saveCrawlingData(List<AiCrawlerItemResponse> dataList) {
        log.info("크롤링된 카페: {}개, 업데이트 진행 중...", dataList.size());

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
            }
        }
        log.info("배치 저장 완료! (성공: {}/전체: {})", count, dataList.size());
    }

    /**
     * 전체 카페에 대한 AI 크롤링 실행 (비동기)
     * DB에서 썸네일이 없는 카페 목록을 배치 단위로 읽어와 AI 서버에 크롤링 요청
     */
    @Async
    public void crawling() {
        // [테스트용] 50개 제한 적용 (필요 시 조절)
        long actualTotalToCrawl = cafeRepository.countByThumbnailUrlIsNull();
        long totalToCrawl = Math.min(actualTotalToCrawl, 50);
        log.info("크롤링 프로세스 시작 (테스트 모드: {}개 제한 / 실제 대상: {}개)", totalToCrawl, actualTotalToCrawl);

        if (totalToCrawl == 0) {
            log.info("수집할 카페가 없습니다.");
            return;
        }

        // 자기 자신을 프록시를 통해 호출하기 위해 Provider에서 가져옴
        CafeCrawlingService self = cafeCrawlingServiceProvider.getIfAvailable();
        if (self == null) {
            log.error("CafeCrawlingService 빈을 찾을 수 없습니다.");
            return;
        }

        // 전체 배치 수 계산 (단일 배치 흐름)
        int totalBatches = (int) Math.ceil((double) totalToCrawl / BATCH_SIZE);

        for (int i = 0; i < totalBatches; i++) {
            int currentBatchNum = i + 1;
            log.info("[배치 {}/{}] 데이터 {}개 조회 중...", currentBatchNum, totalBatches, BATCH_SIZE);

            // 잔여 대상 중 상위 BATCH_SIZE(50)개 조회
            Page<CafeEntity> cafePage = cafeRepository.findAllByThumbnailUrlIsNull(PageRequest.of(0, BATCH_SIZE));
            List<CafeEntity> currentBatch = cafePage.getContent();

            if (currentBatch.isEmpty()) {
                log.info("더 이상 수집할 데이터 없음.");
                break;
            }

            // AI 서버 요청용 DTO 변환
            List<AiCrawlerRequestDto> requestBatch = currentBatch.stream()
                    .map(AiCrawlerRequestDto::from)
                    .collect(Collectors.toList());

            try {
                log.info("[배치 {}/{}] AI 서버 요청 전송... ({}건)", currentBatchNum, totalBatches, requestBatch.size());
                AiCrawlerResponse response = aiCrawlerApiClient.crawl(requestBatch);

                if (response != null && response.getItems() != null && !response.getItems().isEmpty()) {
                    log.info("[배치 {}/{}] {}건 수신 성공, DB 저장을 시작합니다.", currentBatchNum, totalBatches,
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
                        log.warn("[배치 {}/{}] AI 크롤링 누락 대상 ({}건): {}",
                                currentBatchNum, totalBatches, missingCafeInfo.size(), missingCafeInfo);
                    }
                } else {
                    log.warn("[배치 {}/{}] AI 서버 응답이 없거나 비어있습니다.", currentBatchNum, totalBatches);
                }
            } catch (Exception e) {
                log.error("[배치 {}/{}] 크롤링 작업 중 예외 발생: {}", currentBatchNum, totalBatches, e.getMessage());
            }

            // 배치 간 지연 시간 추가 (AI 서버 부하 방지용, 필요 시 조절)
            if (i < totalBatches - 1) {
                try {
                    log.info("다음 배치를 위해 5초간 대기합니다...");
                    Thread.sleep(5000);
                } catch (InterruptedException e) {
                    Thread.currentThread().interrupt();
                    log.warn("대기 중 인터럽트 발생: {}", e.getMessage());
                }
            }
        }

        log.info("모든 크롤링 작업이 종료되었습니다.");
    }
}


