package com.degging.be.cafe.service;

import com.degging.be.infra.ai.dto.request.AiSearchRequest;
import com.degging.be.cafe.dto.request.CafeSearchRequest;
import com.degging.be.infra.ai.dto.response.AiSearchResponse;
import com.degging.be.cafe.dto.response.internal.CafeSearchResponse;
import com.degging.be.cafe.entity.CafeEntity;
import com.degging.be.cafe.repository.CafeRepository;
import com.degging.be.cafe.repository.VibeRepository;
import com.degging.be.global.event.KafkaProducer;
import com.degging.be.global.event.SearchEvent;
import com.degging.be.user.entity.mongodb.UserOnboarding;
import com.degging.be.user.repository.mongodb.UserOnboardingRepository;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.data.mongodb.core.MongoTemplate;
import org.springframework.data.mongodb.core.query.Criteria;
import org.springframework.data.mongodb.core.query.Update;
import org.springframework.data.redis.core.RedisTemplate;
import org.springframework.scheduling.annotation.Async;
import org.springframework.stereotype.Service;
import com.degging.be.infra.ai.AiClient;

import org.springframework.data.mongodb.core.query.Query;
import java.time.Duration;
import java.util.*;

/**
 * 검색 관련 서비스 클래스
 */
@Slf4j
@Service
@RequiredArgsConstructor
public class CafeSearchService {

    private final AiClient aiClient; // AI 서버와 통신용
    private final RedisTemplate<String, Object> redisTemplate;
    private final CafeRepository cafeRepository;
    private final VibeRepository vibeRepository;
    private final KafkaProducer kafkaProducer;
    private final UserOnboardingRepository userOnboardingRepository;

    private final String TOPIC_NAME = "degging.cafe.search.events"; // kafka topic 명
    private final MongoTemplate mongoTemplate;


    /**
     * 프론트엔드 검색 시작 - AI 처리 전 수신 확인용
     * @param request 프론트엔드가 보낸 원본 검색어 및 좌표
     * @return AI 분석 결과
     */
    public CafeSearchResponse processSearch(UUID userId, CafeSearchRequest request) {
        // request 속 mood 를 tag_name (자연어) -> tag_id (UUID) 로 맵핑
        List<UUID> tagIds = extractTagIds(request.getMood());

        // 검색된 분위기 태그를 유저 취향에 반영 (MongoDB)
        updateUserPreferencesAsync(userId, tagIds);

        // AI 서버 호출
        AiSearchRequest aiSearchRequest = AiSearchRequest.of(userId, request, tagIds);
        AiSearchResponse res = aiClient.search(aiSearchRequest);

        // AI가 대답을 했다면, 결과가 0개여도 사용자의 의도는 기록으로 남김
        publishSearchEventsAndLogs(userId, request.getKeyword(), res);

        // 결과 검증 및 카페 목록 조회/정렬
        List<CafeSearchResponse.CafeSearchItem> items = fetchAndSortCafes(request, res);

        // DTO 반환 및 결과 캐싱
        if (!items.isEmpty()) {
            saveRecommendCache(userId, items);
        }

        return CafeSearchResponse.builder().cafes(items).build();
    }

    /**
     * 자연어 Mood에서 태그 UUID 추출
     */
    private List<UUID> extractTagIds(List<String> mood) {
        if (mood == null || mood.isEmpty()) {
            return Collections.emptyList();
        }

        List<UUID> tagIds = vibeRepository.findTagIdByTagNames(mood);
        log.info("[검색 request Ids] 추출된 태그 개수: {}", tagIds.size());
        return tagIds;
    }

    /**
     * MongoDB 유저 취향 점수 업데이트 (비동기 처리)
     */
    @Async("threadPoolTaskExecutor") // 이미 존재하는 스레드풀 활용
    public void updateUserPreferencesAsync(UUID userId, List<UUID> tagIds) {
        if (tagIds.isEmpty()) return;

        String stringUserId = userId.toString();
        for (UUID tagId : tagIds) {
            incrementTagScore(stringUserId, tagId.toString());
        }
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

    /**
     * 검색 관련 이벤트(Kafka) 및 로그(Redis) 처리
     */
    private void publishSearchEventsAndLogs(UUID userId, String keyword, AiSearchResponse res) {
        if (res == null) return;

        // 검색 이벤트 발행 (메뉴가 추출된 경우만)
        if (res.getExtractedMenus() != null && !res.getExtractedMenus().isEmpty()) {
            kafkaProducer.send(TOPIC_NAME, SearchEvent.of(res.getExtractedMenus(), userId));
        }

        // 검색 로그 저장
        saveSearchLog(userId, keyword);
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

    /**
     * 유저의 특정 태그 점수를 1점 올림
     */
    @Async
    public void incrementTagScore(String userId, String tagId) {
        // 필드명을 엔티티의 @Field 값인 "user_id"와 "preferred_tags"로 맞춰주세요.
        Query query = new Query(Criteria.where("user_id").is(userId));
        Update update = new Update().inc("preferred_tags." + tagId, 1);

        mongoTemplate.upsert(query, update, UserOnboarding.class);
        log.info("[MongoDB] 취향 점수 반영 완료 - User: {}, Tag: {}", userId, tagId);
    }

    /**
     * 4. AI 응답 기반으로 카페 DB 조회 후 DTO 변환 및 정렬
     */
    private List<CafeSearchResponse.CafeSearchItem> fetchAndSortCafes(CafeSearchRequest request, AiSearchResponse res) {
        if (res == null || res.getCafeIds() == null || res.getCafeIds().isEmpty()) {
            log.warn("AI 응답이 비어있습니다. 빈 결과를 반환합니다.");
            return Collections.emptyList();
        }

        List<CafeEntity> cafeList = cafeRepository.findAllById(res.getCafeIds());
        if (cafeList.isEmpty()) {
            return Collections.emptyList();
        }

        return cafeList.stream()
                .map(cafe -> CafeSearchResponse.CafeSearchItem.from(
                        cafe,
                        request.getLatitude(),
                        request.getLongitude()
                ))
                // DTO 내부의 getCafeRank를 사용하여 AI 순위대로 정렬
                .sorted(Comparator.comparingInt(item ->
                        res.getCafeRank(item.getCafeId().toString())
                ))
                .toList();
    }

}
