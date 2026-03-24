package com.degging.be.cafe.service;

import com.degging.be.cafe.client.AiCrawlerApiClient;
import com.degging.be.cafe.dto.request.AiCrawlerRequestDto;
import com.degging.be.cafe.dto.response.external.AiCrawlerItemResponse;
import com.degging.be.cafe.dto.response.external.AiCrawlerResponse;
import com.degging.be.cafe.entity.CafeEntity;
import com.degging.be.cafe.repository.CafeRepository;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
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

    private static final int BATCH_SIZE = 100;

    /**
     * 전달받은 크롤링 데이터 DB에 반영 (비동기 수행)
     */
    @Async
    public void processCrawlingData(List<AiCrawlerItemResponse> dataList) {
        log.info("Starting bulk update for {} crawled cafes...", dataList.size());

        for (AiCrawlerItemResponse dto : dataList) {
            try {
                cafeCrawlingUpdateService.updateSingleCafe(dto);
            } catch (Exception e) {
                log.error("Failed to update cafe data for cafeId: {}. Error: {}", 
                        (dto.getCafes() != null ? dto.getCafes().getCafeId() : "unknown"), e.getMessage());
            }
        }
        log.info("Finished processing crawling data.");
    }

    /**
     * 전체 카페에 대한 AI 크롤링 트리거 (비동기)
     * DB에서 썸네일이 없는 카페 목록을 100개씩 읽어와 AI 서버에 크롤링 요청
     */
    @Async
    public void triggerFullCrawling() {
        log.info("Starting full AI crawling trigger (Target: cafes without thumbnails)...");

        int pageNum = 0;
        long totalProcessed = 0;
        Page<CafeEntity> cafePage;

        do {
            // DB에서 크롤링이 필요한(썸네일 없는) 카페 목록 100개씩 조회
            cafePage = cafeRepository.findAllByThumbnailUrlIsNull(PageRequest.of(0, BATCH_SIZE));
            List<CafeEntity> cafes = cafePage.getContent();

            if (cafes.isEmpty()) break;

            // AI 서버 요청 DTO로 변환
            List<AiCrawlerRequestDto> requestBatch = cafes.stream()
                    .map(AiCrawlerRequestDto::from)
                    .collect(Collectors.toList());

            // AI 서버 호출
            log.info("Crawling batch {} (size: {})", pageNum + 1, requestBatch.size());
            AiCrawlerResponse response = aiCrawlerApiClient.crawl(requestBatch);

            // 수집된 데이터 저장 (processCrawlingData 호출)
            if (response != null && response.getItems() != null && !response.getItems().isEmpty()) {
                this.processCrawlingData(response.getItems());
                
                if (response.getMissingCafeIds() != null && !response.getMissingCafeIds().isEmpty()) {
                    log.warn("AI server could not find data for {} cafes in batch {}", 
                            response.getMissingCafeIds().size(), pageNum + 1);
                }
            } else {
                log.warn("Empty or null response from AI server for batch {}", pageNum + 1);
            }

            totalProcessed += cafes.size();
            pageNum++;
            
            // 처리가 완료된 카페는 thumbnailUrl이 채워져 다음 조회 대상(null)에서 제외
            // 따라서 매번 0페이지를 요청하여 새로운 '미수집' 카페 100건을 가져옴

        } while (cafePage.hasNext() && pageNum < 500); // 무한 루프 방지 안전장치

        log.info("Full AI crawling trigger finished. Total cafes sent: {}", totalProcessed);
    }
}
