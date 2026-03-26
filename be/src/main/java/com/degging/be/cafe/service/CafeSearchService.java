package com.degging.be.cafe.service;

import com.degging.be.cafe.dto.request.AiSearchRequest;
import com.degging.be.cafe.dto.request.CafeSearchRequest;
import com.degging.be.cafe.dto.response.external.AiSearchResponse;
import com.degging.be.cafe.dto.response.internal.CafeSearchResponse;
import com.degging.be.cafe.entity.CafeEntity;
import com.degging.be.cafe.repository.CafeRepository;
import com.degging.be.cafe.repository.VibeRepository;
import com.degging.be.global.event.KafkaProducer;
import com.degging.be.global.event.SearchEvent;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.data.redis.core.RedisTemplate;
import org.springframework.scheduling.annotation.Async;
import org.springframework.stereotype.Service;
import org.springframework.web.reactive.function.client.WebClient;
import reactor.core.publisher.Mono;

import java.time.Duration;
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
    private final CafeRepository cafeRepository;
    private final VibeRepository vibeRepository;
    private final KafkaProducer kafkaProducer;

    private final String TOPIC_NAME = "degging.cafe.search.events"; // kafka topic 명

    @Value("${ai.server.url}")
    private String aiServerUrl;

    /**
     * 프론트엔드 검색 시작 - AI 처리 전 수신 확인용
     * @param request 프론트엔드가 보낸 원본 검색어 및 좌표
     * @return AI 분석 결과
     */
    public CafeSearchResponse processSearch(UUID userId, CafeSearchRequest request) {
        // request 속 mood 를 tag_name (자연어) -> tag_id (UUID) 로 맵핑
        List<UUID> tagIds = vibeRepository.findTagIdByTagNames(request.getMood());
        AiSearchRequest aiSearchRequest = AiSearchRequest.of(userId, request, tagIds);

        // AI 서버 호출
        AiSearchResponse res = aiWebClient.post()
                .uri(aiServerUrl  + "/ai/map/search")
                .bodyValue(aiSearchRequest)
                .retrieve()
                .bodyToMono(AiSearchResponse.class)// 응답 형식
                // 에러 발생 시 빈 결과 반환
                .onErrorResume(e -> {
                    log.error("AI 서버 호출 실패: {}", e.getMessage());
                    return Mono.just(AiSearchResponse.empty());
                })
                .block();
//                .block(Duration.ofSeconds(5)); // 결과 나올 때까지 동기 방식으로 대기, 5초까지만 대기

        // AI가 대답을 했다면, 결과가 0개여도 사용자의 의도는 기록으로 남김
        if (res != null){
            // 검색 이벤트 발행 -> 랭크 도메인에서 받아 실시간 트랜드 반영
            if (res.getExtractedMenus() != null && !res.getExtractedMenus().isEmpty()) {
                kafkaProducer.send(TOPIC_NAME, SearchEvent.of(res.getExtractedMenus(), userId));
            }

            // 개인 검색 로그 저장 호출
            saveSearchLog(userId, request.getKeyword());
        }

        // AI 응답 검증
        if (res == null || res.getCafeIds() == null || res.getCafeIds().isEmpty()){
            log.warn("AI 응답이 비어있습니다. 빈 결과를 반환합니다. User: {}", userId);
            return CafeSearchResponse.builder()
                    .cafes(Collections.emptyList())
                    .build();
        }

        // DB 에서 추천 카페 상세정보 조회
        List<CafeEntity> cafeList = cafeRepository.findAllById(res.getCafeIds());

        if (cafeList.isEmpty()) {
            return CafeSearchResponse.builder().cafes(Collections.emptyList()).build();
        }

        // DTO 로 변환 및 추천 순서대로 정렬
        List<CafeSearchResponse.CafeSearchItem> items = cafeList.stream()
                .map(cafe -> CafeSearchResponse.CafeSearchItem.from(
                        cafe, request.getLatitude(),
                        request.getLongitude()
                ))
                // AI 응답에 있는 sortNum 에 따라 정렬하는데,
                /* NPE 방어: AI 결과 맵에 ID가 없으면 가장 뒤 순위(999)로 밀어냄
               res.getCafes()가 Map<UUID, Integer> 형태라고 가정할 때 안전함
                */
                .sorted(Comparator.comparingInt(item ->
                        res.getCafes().getOrDefault(item.getCafeId(), 999)))
                .toList();

        // 비동기로 추천 결과 캐싱  10분 저장
        saveRecommendCache(userId, items);

        // TODO : 유저 취향 태그 반영
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
