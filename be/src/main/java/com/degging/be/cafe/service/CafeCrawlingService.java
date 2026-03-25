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
import org.springframework.transaction.annotation.Transactional;

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

    // 프록시를 통한 자기 자신 호출을 위한 지연 주입
    private final ObjectProvider<CafeCrawlingService> cafeCrawlingServiceProvider;

    private static final int BATCH_SIZE = 100;

    /**
     * 수집된 데이터를 DB에 저장 (배치 단위로 트랜잭션 처리)
     */
    @Transactional
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
     * DB에서 썸네일이 없는 카페 목록을 100개씩 읽어와 AI 서버에 크롤링 요청
     */
    @Async
    public void crawling() {
        // 전체 데이터 개수 확인
        long totalToCrawl = cafeRepository.countByThumbnailUrlIsNull();
        log.info("AI 크롤링 프로세스 시작 (전체 대상: {}개)", totalToCrawl);

        if (totalToCrawl == 0) {
            log.info("수집할 카페가 없습니다.");
            return;
        }

        // 자기 자신을 프록시를 통해 호출하기 위해 Provider에서 가져옴
        CafeCrawlingService self = cafeCrawlingServiceProvider.getIfAvailable();

        // 전체 배치 수 계산 후 루프 실행
        int totalBatches = (int) Math.ceil((double) totalToCrawl / BATCH_SIZE);

        for (int i = 0; i < totalBatches; i++) {
            log.info("[배치 {}/{}] 데이터 조회 중...", i + 1, totalBatches);

            // 잔여 대상 중 상위 100개 조회
            Page<CafeEntity> cafePage = cafeRepository.findAllByThumbnailUrlIsNull(PageRequest.of(0, BATCH_SIZE));
            List<CafeEntity> cafes = cafePage.getContent();

            if (cafes.isEmpty()) {
                log.info("더 이상 수집할 데이터 없음.");
                break;
            }

            // AI 서버 요청 전송
            List<AiCrawlerRequestDto> requestBatch = cafes.stream()
                    .map(AiCrawlerRequestDto::from)
                    .collect(Collectors.toList());

            log.info("[배치 {}/{}] AI 서버 요청 전송... ({}건)", i + 1, totalBatches, requestBatch.size());

            try {
                AiCrawlerResponse response = aiCrawlerApiClient.crawl(requestBatch);

                if (response != null && response.getItems() != null && !response.getItems().isEmpty()) {
                    log.info("[배치 {}/{}] {}건 수신 성공, DB 저장을 시작합니다.", i + 1, totalBatches, response.getItems().size());

                    // 프록시 객체(self)를 통해 호출하여 @Transactional 동작 보장
                    if (self != null) {
                        self.saveCrawlingData(response.getItems());
                    } else {
                        log.error("CafeCrawlingService 빈을 찾을 수 없어 저장을 중단합니다.");
                        break;
                    }

                    // 누락된 카페 ID 로깅 추가 (카페명 포함)
                    if (response.getMissingCafeIds() != null && !response.getMissingCafeIds().isEmpty()) {
                        List<CafeEntity> missingCafes = cafeRepository.findAllById(response.getMissingCafeIds());
                        List<String> missingCafeInfo = missingCafes.stream()
                                .map(c -> c.getName() + "(" + c.getCafeId() + ")")
                                .collect(Collectors.toList());
                        
                        log.warn("[배치 {}/{}] AI 크롤링 누락 대상 ({}건): {}", 
                                i + 1, totalBatches, missingCafeInfo.size(), missingCafeInfo);
                    }
                } else {
                    log.warn("[배치 {}/{}] AI 서버 응답이 없음. 작업 중단.", i + 1, totalBatches);
                    break;
                }
            } catch (Exception e) {
                log.error("[배치 {}/{}] 크롤링 실패: {}. 작업 중단.", i + 1, totalBatches, e.getMessage());
                break;
            }
        }

        log.info("모든 AI 크롤링 작업이 종료되었습니다.");
    }
}
