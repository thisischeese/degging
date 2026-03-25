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

import java.util.ArrayList;
import java.util.List;
import java.util.concurrent.CompletableFuture;
import java.util.concurrent.TimeUnit;
import java.util.stream.Collectors;
import java.util.stream.IntStream;

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
    private static final int BATCH_START_DELAY_SECONDS = 2; // 배치 간 요청 시작 딜레이

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
     * DB에서 썸네일이 없는 카페 목록을 400개(4개 워커 분량)씩 읽어와 AI 서버에 병렬로 크롤링 요청
     */
    @Async
    public void crawling() {
        // [기존 코드] 전체 데이터 개수 확인
        // long totalToCrawl = cafeRepository.countByThumbnailUrlIsNull();
        // log.info("크롤링 프로세스 시작 (전체 대상: {}개)", totalToCrawl);

        // [테스트용] 1000개 제한 적용
        long actualTotalToCrawl = cafeRepository.countByThumbnailUrlIsNull();
        long totalToCrawl = Math.min(actualTotalToCrawl, 1000);
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

        // 한 루프에서 처리할 양 (4개 워커 * 배치 사이즈 50)
        final int WORKERS = 4;
        final int TOTAL_PER_LOOP = BATCH_SIZE * WORKERS;

        int totalLoops = (int) Math.ceil((double) totalToCrawl / TOTAL_PER_LOOP);

        for (int loop = 0; loop < totalLoops; loop++) {
            log.info("[루프 {}/{}] 데이터 {}개 조회 중...", loop + 1, totalLoops, TOTAL_PER_LOOP);

            // 잔여 대상 중 상위 400개 조회
            Page<CafeEntity> cafePage = cafeRepository.findAllByThumbnailUrlIsNull(PageRequest.of(0, TOTAL_PER_LOOP));
            List<CafeEntity> allCafesInLoop = cafePage.getContent();

            if (allCafesInLoop.isEmpty()) {
                log.info("더 이상 수집할 데이터 없음.");
                break;
            }

            // 조회된 데이터를 100개씩 4개 배치로 분할
            List<List<CafeEntity>> batches = IntStream.range(0, (allCafesInLoop.size() + BATCH_SIZE - 1) / BATCH_SIZE)
                    .mapToObj(i -> allCafesInLoop.subList(i * BATCH_SIZE,
                            Math.min(allCafesInLoop.size(), (i + 1) * BATCH_SIZE)))
                    .collect(Collectors.toList());

            log.info("[루프 {}/{}] {}개의 워커로 병렬 요청 시작 (총 {}건)", loop + 1, totalLoops, batches.size(),
                    allCafesInLoop.size());

            // 각 배치를 병렬로 처리 (배치 시작 전 딜레이로 AI 서버 부하 분산)
            List<CompletableFuture<Void>> futures = new ArrayList<>();
            for (int i = 0; i < batches.size(); i++) {
                final int batchIdx = i + 1;
                final List<CafeEntity> currentBatch = batches.get(i);
                final int currentLoop = loop + 1;

                // 배치 시작 간격 (첫 배치 제외)
                if (i > 0) {
                    try {
                        log.info("[루프 {}/워커 {}] {}초 후 요청 시작...", currentLoop, batchIdx, BATCH_START_DELAY_SECONDS);
                        TimeUnit.SECONDS.sleep(BATCH_START_DELAY_SECONDS);
                    } catch (InterruptedException e) {
                        Thread.currentThread().interrupt();
                        log.warn("배치 딜레이 중 인터럽트 발생: {}", e.getMessage());
                    }
                }

                futures.add(CompletableFuture.runAsync(() -> {
                    // AI 서버 요청용 DTO 변환
                    List<AiCrawlerRequestDto> requestBatch = currentBatch.stream()
                            .map(AiCrawlerRequestDto::from)
                            .collect(Collectors.toList());

                    try {
                        log.info("[루프 {}/워커 {}] AI 서버 요청 전송... ({}건)", currentLoop, batchIdx, requestBatch.size());
                        AiCrawlerResponse response = aiCrawlerApiClient.crawl(requestBatch);

                        if (response != null && response.getItems() != null && !response.getItems().isEmpty()) {
                            log.info("[루프 {}/워커 {}] {}건 수신 성공, DB 저장을 시작합니다.", currentLoop, batchIdx,
                                    response.getItems().size());

                            // AI 응답 즉시 JSON 백업 (DB 저장 실패 대비)
                            crawlingBackupService.backup(response, currentLoop, batchIdx);

                            // 프록시 객체(self)를 통해 트랜잭션 보장하며 저장
                            self.saveCrawlingData(response.getItems());

                            // 누락된 카페 ID 로깅 (카페명 포함)
                            if (response.getMissingCafeIds() != null && !response.getMissingCafeIds().isEmpty()) {
                                List<CafeEntity> missingCafes = cafeRepository
                                        .findAllById(response.getMissingCafeIds());
                                List<String> missingCafeInfo = missingCafes.stream()
                                        .map(c -> c.getName() + "(" + c.getCafeId() + ")")
                                        .collect(Collectors.toList());
                                log.warn("[루프 {}/워커 {}] AI 크롤링 누락 대상 ({}건): {}",
                                        currentLoop, batchIdx, missingCafeInfo.size(), missingCafeInfo);
                            }
                        } else {
                            log.warn("[루프 {}/워커 {}] AI 서버 응답이 없거나 비어있습니다.", currentLoop, batchIdx);
                        }
                    } catch (Exception e) {
                        log.error("[루프 {}/워커 {}] 크롤링 작업 중 예외 발생: {}", currentLoop, batchIdx, e.getMessage());
                    }
                }));
            }

            // 모든 워커가 이 루프의 작업을 마칠 때까지 대기
            CompletableFuture.allOf(futures.toArray(new CompletableFuture[0])).join();

            log.info("[루프 {}/{}] 모든 워커 작업 완료", loop + 1, totalLoops);

            // 다음 루프 시작 전 지연 시간 추가 (AI 서버 부하 방지)
            if (loop < totalLoops - 1) {
                log.info("다음 루프 시작 전 60초간 대기합니다...");
                try {
                    Thread.sleep(60000);
                } catch (InterruptedException e) {
                    Thread.currentThread().interrupt();
                    log.warn("대기 중 인터럽트 발생: {}", e.getMessage());
                }
            }
        }

        log.info("모든 크롤링 병렬 작업이 종료되었습니다.");
    }
}
