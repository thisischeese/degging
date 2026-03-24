package com.degging.be.cafe.client;

import com.degging.be.cafe.dto.request.AiCrawlerRequestDto;
import com.degging.be.cafe.dto.response.external.AiCrawlerResponse;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import com.degging.be.global.exception.BaseException;
import com.degging.be.global.exception.errorcode.CommonErrorCode;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.http.MediaType;
import org.springframework.stereotype.Component;
import org.springframework.web.reactive.function.client.WebClient;
import java.util.List;

/**
 * 크롤러 호출 클라이언트
 */
@Slf4j
@Component
@RequiredArgsConstructor
public class AiCrawlerApiClient {

    private final WebClient webClient;

    @Value("${ai.server.url}")
    private String aiServerUrl;

    /**
     * AI 서버에 카페 목록 크롤링 요청 전송
     *
     * @param requestList 크롤링 대상 카페 기본 정보 리스트
     * @return AI 서버 응답 (크롤링 결과 및 누락 ID 목록)
     */
    public AiCrawlerResponse crawl(List<AiCrawlerRequestDto> requestList) {
        log.info("Sending crawl request for {} cafes to AI server at {}", requestList.size(), aiServerUrl);

        try {
            return webClient.post()
                    .uri(aiServerUrl + "/ai/cafes/crawling")
                    .contentType(MediaType.APPLICATION_JSON)
                    .bodyValue(requestList)
                    .accept(MediaType.APPLICATION_JSON)
                    .retrieve()
                    .bodyToMono(AiCrawlerResponse.class)
                    .block();
        } catch (Exception e) {
            log.error("AI crawler API 호출 중 오류 발생: {}", e.getMessage());
            throw new BaseException(CommonErrorCode.EXTERNAL_API_ERROR);
        }
    }
}
