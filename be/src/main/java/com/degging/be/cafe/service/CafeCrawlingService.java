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
    public void saveCrawlingData(List<AiCrawlerItemResponse> dataList) {
        log.info("크롤링된 카페: {}개, 업데이트 시작...", dataList.size());

        for (AiCrawlerItemResponse dto : dataList) {
            try {
                cafeCrawlingUpdateService.updateSingleCafe(dto);
            } catch (Exception e) {
                log.error("카페 데이터 업데이트 실패 (cafeId: {}). 에러: {}",
                        (dto.getCafes() != null ? dto.getCafes().getCafeId() : "unknown"), e.getMessage());
            }
        }
        log.info("크롤링 데이터 배치 처리 완료. 다음 배치 요청...");

        // 다음 배치를 수집하기 위해 crawling() 다시 호출
        this.crawling();
    }

    /**
     * 전체 카페에 대한 AI 크롤링 실행 (비동기)
     * DB에서 썸네일이 없는 카페 목록을 100개씩 읽어와 AI 서버에 크롤링 요청
     */
    @Async
    public void crawling() {
        log.info("AI 크롤링 배치 요청을 시작합니다 (대상: 썸네일 없는 카페)...");

        // DB에서 크롤링이 필요한(썸네일 없는) 카페 목록 100개 조회
        Page<CafeEntity> cafePage = cafeRepository.findAllByThumbnailUrlIsNull(PageRequest.of(0, BATCH_SIZE));
        List<CafeEntity> cafes = cafePage.getContent();

        if (cafes.isEmpty()) {
            log.info("썸네일 수집할 카페가 없음. 프로세스 종료.");
            return;
        }

        // AI 서버 요청 DTO로 변환
        List<AiCrawlerRequestDto> requestBatch = cafes.stream()
                .map(AiCrawlerRequestDto::from)
                .collect(Collectors.toList());

        // AI 서버 호출
        log.info("AI 서버로 배치 전송 중 (크기: {})", requestBatch.size());

        try {
            AiCrawlerResponse response = aiCrawlerApiClient.crawl(requestBatch);

            // 수집된 데이터 저장 (성공 시 saveCrawlingData 호출)
            if (response != null && response.getItems() != null && !response.getItems().isEmpty()) {
                log.info("{}개 수신", response.getItems().size());
                this.saveCrawlingData(response.getItems());

                if (response.getMissingCafeIds() != null && !response.getMissingCafeIds().isEmpty()) {
                    log.warn("미수집 카페: {}개",
                            response.getMissingCafeIds().size());
                }
            } else {
                log.warn("AI 서버 비어있거나 올바르지 않은 응답");
            }
        } catch (Exception e) {
            log.error("AI 크롤러 API 호출 중 오류 발생: {}", e.getMessage());
        }
    }
}
