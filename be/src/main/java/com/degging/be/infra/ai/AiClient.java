package com.degging.be.infra.ai;

import com.degging.be.infra.ai.dto.request.AiCrawlerRequestDto;
import com.degging.be.infra.ai.dto.request.AiSearchRequest;
import com.degging.be.infra.ai.dto.response.AiCrawlerResponse;
import com.degging.be.infra.ai.dto.response.AiSearchResponse;
import com.degging.be.discovery.dto.request.AIDiscoveryRequest;
import com.degging.be.discovery.dto.response.AIDiscoveryResponse;
import com.degging.be.global.exception.BaseException;
import com.degging.be.global.exception.errorcode.CommonErrorCode;
import com.degging.be.user.dto.request.AiOnboardingRequest;
import com.degging.be.user.dto.response.AiOnboardingResponse;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.http.MediaType;
import org.springframework.stereotype.Component;
import org.springframework.web.reactive.function.client.WebClient;
import reactor.core.publisher.Mono;

import java.util.Collections;
import java.util.List;
import java.util.Map;
import java.util.UUID;

/**
 * AI 서버와의 모든 통신을 담당하는 통합 클라이언트
 */
@Slf4j
@Component
@RequiredArgsConstructor
public class AiClient {

    private final WebClient webClient;

    @Value("${ai.server.url}")
    private String aiServerUrl;

    /**
     * 크롤링 요청 (Crawling)
     * 
     * @param requestList 크롤링할 카페 목록
     * @return AiCrawlerResponse 크롤링 결과
     */
    public AiCrawlerResponse crawl(List<AiCrawlerRequestDto> requestList) {
        log.info("AI 서버 크롤링 요청 전송 (개수: {})", requestList.size());

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

    /**
     * 지도 검색 분석 요청 (Search)
     * 
     * @param aiSearchRequest 지도 검색 요청 DTO
     * @return AiSearchResponse 지도 검색 결과
     */
    public AiSearchResponse search(AiSearchRequest aiSearchRequest) {
        log.info("AI 서버 검색 요청 전송");

        try {
            return webClient.post()
                    .uri(aiServerUrl + "/ai/map/search")
                    .bodyValue(aiSearchRequest)
                    .retrieve()
                    .bodyToMono(AiSearchResponse.class)
                    .onErrorResume(e -> {
                        log.error("AI 검색 API 호출 실패: {}", e.getMessage());
                        return Mono.just(AiSearchResponse.empty());
                    })
                    .block();
        } catch (Exception e) {
            log.error("AI 검색 API 호출 중 예외 발생: {}", e.getMessage());
            return AiSearchResponse.empty();
        }
    }

    /**
     * 사용자 맞춤 추천 목록 요청 (Discovery)
     * 
     * @param userId 사용자 ID
     * @return Map<UUID, Integer> 카페 ID와 추천 순위
     */
    public Map<UUID, Integer> getDiscoveryRecommendations(UUID userId) {
        log.info("AI 서버 추천 목록 요청 (user_id: {})", userId);

        try {
            AIDiscoveryResponse response = webClient.post()
                    .uri(aiServerUrl + "/ai/discovery")
                    .bodyValue(new AIDiscoveryRequest(userId))
                    .retrieve()
                    .bodyToMono(AIDiscoveryResponse.class)
                    .block();

            if (response != null && response.getCafes() != null) {
                return response.getCafes();
            }
        } catch (Exception e) {
            log.error("AI 추천 API 호출 중 오류 발생: {}", e.getMessage());
        }

        return Collections.emptyMap();
    }

    /**
     * 온보딩 결과 전송 (Onboarding)
     *
     * @param request 온보딩 요청 DTO (user_id, cafe_id_list, menu_id_list)
     * @return AiOnboardingResponse AI 서버 처리 결과, 실패 시 null
     */
    public AiOnboardingResponse sendOnboarding(AiOnboardingRequest request) {
        log.info("AI 서버 온보딩 요청 전송 (user_id: {})", request.getUser_id());

        try {
            return webClient.post()
                    .uri(aiServerUrl + "/ai/onboarding")
                    .contentType(MediaType.APPLICATION_JSON)
                    .bodyValue(request)
                    .accept(MediaType.APPLICATION_JSON)
                    .retrieve()
                    .bodyToMono(AiOnboardingResponse.class)
                    .block();
        } catch (Exception e) {
            log.error("AI 온보딩 API 호출 중 오류 발생: {}", e.getMessage());
            return null;
        }
    }
}
