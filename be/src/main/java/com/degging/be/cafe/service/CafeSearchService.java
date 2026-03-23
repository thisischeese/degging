package com.degging.be.cafe.service;

import com.degging.be.cafe.dto.request.CafeSearchRequest;
import com.degging.be.cafe.dto.response.external.AiSearchResponse;
import com.degging.be.cafe.dto.response.internal.CafeSearchResponse;
import com.degging.be.cafe.entity.CafeEntity;
import com.degging.be.cafe.repository.CafeRepository;
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
    private final CafeRepository cafeRepository;

    /**
     * 프론트엔드 검색 시작 - AI 처리 전 수신 확인용
     * @param request 프론트엔드가 보낸 원본 검색어 및 좌표
     * @return AI 분석 결과
     */
    public CafeSearchResponse processSearch(UUID userId, CafeSearchRequest request) {
        // AI 서버 호출
        /* AI 서버 연동 전 주석 처리
        AiSearchResponse res = aiWebClient.post()
                .uri("/ai/map/search")
                .bodyValue(request)
                .retrieve()
                .bodyToMono(AiSearchResponse.class)// 응답 형식
                .block(Duration.ofSeconds(5)); // 결과 나올 때까지 동기 방식으로 대기, 5초까지만 대기
        */

        // 테스트를 위한 mock 응답 데이터
        AiSearchResponse res = AiSearchResponse.builder()
                .cafes(Map.of(UUID.fromString("c5383afd-48e0-48f1-863b-33ccd638b410"), 1))
                .extractedMenus(Map.of("1234", 3, "5678", 1))
                .menuCount(2)
                .build();

        // AI 응답 검증
        if (res == null || res.getCafeIds() == null || res.getCafeIds().isEmpty()){
            log.warn("AI 응답이 비어있습니다. 빈 결과를 반환합니다. User: {}", userId);
            return CafeSearchResponse.builder()
                    .cafes(Collections.emptyList())
                    .build();
        }

        // DB 에서 추천 카페 상세정보 조회
        List<CafeEntity> cafeList = cafeRepository.findAllById(res.getCafeIds());

        // DTO 로 변환 및 추천 순서대로 정렬
        List<CafeSearchResponse.CafeSearchItem> items = cafeList.stream()
                .map(cafe -> CafeSearchResponse.CafeSearchItem.from(
                        cafe, request.getLatitude(),
                        request.getLongitude()
                ))
                // AI 응답에 있는 sortNum 에 따라 정렬
                .sorted(Comparator.comparingInt(item -> res.getCafes().get(item.getCafeId())))
                .toList();

        // 추천 결과 캐싱, 10분 저장
        redisTemplate.opsForValue().set("cache:search:" + userId, items, Duration.ofMinutes(10));

        // 비동기로 추천 결과 캐싱
        saveRecommendCache(userId, items);

        // 검색 이벤트 발행 -> 랭크 도메인에서 받아 실시간 트랜드 반영
        if (res.getExtractedMenus() != null && !res.getExtractedMenus().isEmpty()) {
            eventPublisher.publishEvent(new SearchEvent(res.getExtractedMenus()));
        }

        // 개인 검색 로그 저장 호출
        saveSearchLog(userId, request.getKeyword());

        return CafeSearchResponse.builder()
                .cafes(items)
                .build();
    }

    // AI 추천 결과를 Redis 에 저장
    @Async("threadPoolTaskExecutor")
    public void saveRecommendCache(UUID userId,List<CafeSearchResponse.CafeSearchItem> items){
        try {
            String key = "cache:search:" + userId;
            redisTemplate.opsForValue().set(key, items, Duration.ofMinutes(10));
            log.info("사용자 {}의 추천 결과 캐싱 완료", userId);
        } catch (Exception e) {
            log.error("추천 결과 캐싱 중 오류 발생: {}", e.getMessage());
        }
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
