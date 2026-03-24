package com.degging.be.cafe.service;

import com.degging.be.cafe.dto.response.external.AiCrawlerItemResponse;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.scheduling.annotation.Async;
import org.springframework.stereotype.Service;

import java.util.List;

@Slf4j
@Service
@RequiredArgsConstructor
public class CafeCrawlingService {

    private final CafeCrawlingUpdateService cafeCrawlingUpdateService;

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
                log.error("Error updating cafe {}: {}", 
                        (dto.getCafes() != null ? dto.getCafes().getCafeId() : "NULL"), 
                        e.getMessage());
            }
        }

        log.info("Finished processing crawling data.");
    }
}
