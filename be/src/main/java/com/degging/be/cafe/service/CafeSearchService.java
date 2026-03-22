package com.degging.be.cafe.service;

import com.degging.be.cafe.dto.request.CafeSearchRequest;
import com.degging.be.cafe.dto.response.external.AiSearchResponse;
import com.degging.be.global.event.SearchEvent;
import jakarta.validation.constraints.NotBlank;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.context.ApplicationEventPublisher;
import org.springframework.data.redis.core.RedisTemplate;
import org.springframework.scheduling.annotation.Async;
import org.springframework.stereotype.Service;
import org.springframework.web.reactive.function.client.WebClient;

import java.time.Duration;
import java.time.LocalDateTime;
import java.util.*;

/**
 * 검색 관련 서비스 클래스
 */
@Slf4j
@Service
@RequiredArgsConstructor
public class CafeSearchService {

    private final WebClient aiWebClient; // AI 서버와 통신용
    private final RedisTemplate<String, Object> redisTemplate;
    private final ApplicationEventPublisher eventPublisher; // 이벤트 발행자

    /**
     * 프론트엔드 검색 시작 - AI 처리 전 수신 확인용
     * @param request 프론트엔드가 보낸 원본 검색어 및 좌표
     * @return AI 분석 결과
     */
    public Map<String, List<UUID>> processSearch(UUID userId, CafeSearchRequest request) {
        // AI 서버 호출
        AiSearchResponse res = aiWebClient.post()
                .uri("경로")
                .bodyValue(request)
                .retrieve()
                .bodyToMono(AiSearchResponse.class)// 응답 형식
                .block(Duration.ofSeconds(5)); // 결과 나올 때까지 동기 방식으로 대기, 5초까지만 대기

        // AI 응답 검증
        if (res == null || res.getCafeIds() == null || res.getCafeIds().isEmpty()){
            log.warn("AI 응답이 비어있습니다. 빈 결과를 반환합니다. User: {}", userId);
            return Map.of("cafes", Collections.emptyList());
        }

        // 검색 이벤트 발행 -> 랭크 도메인에서 받아 실시간 트랜드 반영
        eventPublisher.publishEvent(new SearchEvent(request.getKeyword()));

        // 개인 검색 로그 저장 호출
        saveSearchLog(userId, request.getKeyword());

        Map<String, List<UUID>> result = new HashMap<>();
        result.put("cafes", res.getCafeIds());

        return result;
    }

    // Redis 에 검색 로그를 저장하는 메서드
    @Async // 별도의 쓰레드에서 실행
    public void saveSearchLog(UUID userId, String keyword) {
        try {
            String logKey = "search:history:" + userId;

            // 가장 앞에 해당 키워드 추가
            redisTemplate.opsForList().leftPush(logKey, keyword);

            // 최근 10개만 유지 (임시. 조율 후 수정)
            redisTemplate.opsForList().trim(logKey, 0, 9);

            // 7일 후 만료 (수정요)
            redisTemplate.expire(logKey, Duration.ofDays(7));

            log.info("[Redis] 유저 {}의 검색 로그 저장 완료: {}", userId, keyword);
        } catch (Exception e) {
            log.error("[Redis Error] 개인 로그 저장 실패. 유저: {}, 사유: {}", userId, e.getMessage());
        }
    }
}
