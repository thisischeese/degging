package com.degging.be.rank.service;

import com.degging.be.global.event.SearchEvent;
import com.degging.be.global.exception.BaseException;
import com.degging.be.global.exception.errorcode.CommonErrorCode;
import com.degging.be.global.exception.errorcode.RankErrorcode;
import com.degging.be.rank.dto.response.RankResponse;
import jakarta.annotation.PostConstruct;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.context.event.EventListener;
import org.springframework.core.io.ClassPathResource;
import org.springframework.data.redis.core.RedisTemplate;
import org.springframework.data.redis.core.StringRedisTemplate;
import org.springframework.scheduling.annotation.Async;
import org.springframework.scheduling.annotation.Scheduled;
import org.springframework.stereotype.Service;

import java.io.BufferedReader;
import java.io.IOException;
import java.io.InputStreamReader;
import java.nio.charset.StandardCharsets;
import java.util.*;
import java.util.stream.IntStream;

/**
  실시간 디저트 순위를 조회하고 변경 사항을 반영하는 클래스
 */
@Slf4j
@Service
@RequiredArgsConstructor
public class RankService {

    private final StringRedisTemplate redisTemplate;

    // Redis 에 실시간 데이터를 저장할 키
    private static final String RANKING_KEY = "dessert_ranking";

    /**
     초기 데이터 Redis 에 적재
     */
    @PostConstruct // 서버 구동 시 자동 실행
    public void initDataFromCSV(){
        log.info("[Redis] 초기 데이터 적재");
        // 해당 키가 존재하는지 확인
        if (Boolean.TRUE.equals(redisTemplate.hasKey(RANKING_KEY))){
            log.info("[Redis] 초기 데이터가 이미 존재하므로 생략");
            return;
        }

        // 설문조사 결과 파일에서 데이터 읽어옴
        try (BufferedReader br = new BufferedReader(new InputStreamReader(
                new ClassPathResource("surveyResult.csv").getInputStream(), StandardCharsets.UTF_8))){

            String line;
            int count = 0;
            while ((line = br.readLine()) != null){
                // 공백 제거 후 , 기준 분리하여 배열 생성
                String[] columns = line.replace("\uFEFF", "").split(",");

                if (columns.length == 2){
                    String dessertName = columns[0].trim();
                    double totalScore = Double.parseDouble(columns[1].trim());
                    // redis 에 적재
                    redisTemplate.opsForZSet().add(RANKING_KEY, dessertName, totalScore);
                    count++;
                }
            }
            log.info("[Redis] 총 {}개의 디저트 랭킹 데이터 초기화 완료", count);
        } catch (IOException e) {
            log.error("[Redis] CSV 파싱 및 적재 중 오류 발생");
            throw new BaseException(CommonErrorCode.FILE_PROCESSING_ERROR);
        }
    }

    /**
     * 실시간 디저트 순위 1~count 위를 조회하는 메서드
     */
    public RankResponse getTopRanks(int count){
        // Redis 에서 내림차순(점수) 1위부터 count 위까지 꺼냄
        Set<String> keywords = redisTemplate.opsForZSet().reverseRange(RANKING_KEY, 0, count-1);

        // 데이터 유효성 검사
        if (keywords.isEmpty()){
            return RankResponse.builder()
                    .rankings(Collections.emptyList())
                    .build(); // 빈 리스트 반환
        }

        // 인덱스 사용을 위해 리스트로 변경
        List<String> keywordList = new ArrayList<>(keywords);

        // 반환을 위해 RankResponse 의 이너클래스 Items 에 맞게 담아줌
        List<RankResponse.Items> items = IntStream.range(0, keywordList.size())
                .mapToObj(i -> RankResponse.Items.builder()
                        .rank(i+1)
                        .keyword(keywordList.get(i))
                        .build())
                .toList();

        // 반환
        return RankResponse.builder()
                .rankings(items)
                .build();
    }

    /**
     * 검색 이벤트 발생 시 점수 반영 (비동기 갱신)
     */
    @Async // 검색 쓰레드와 점수 올리는 쓰레드를 분리
    @EventListener // 이벤트 발행 시 자동 실행
    public void handleSearchEvent(SearchEvent event){
        Map<String, Integer> menus = event.extractedMenus();
        if (menus == null || menus.isEmpty()) return;

        try {
            // 최종 점수 = 기본 점수(1.0) + 시간 가중치
            double baseScore = calculateBaseScore();

            // 메뉴별 점수 반영 로직을 별도 메서드로 분리하여 중첩 제거
            menus.forEach((menuIdStr, aiCount) -> processMenuScore(menuIdStr, aiCount, baseScore));

        } catch (Exception e) {
            log.error("[Rank Error] {} : {}",
                    RankErrorcode.RANKING_PROCESS_ERROR.getCode(),
                    RankErrorcode.RANKING_PROCESS_ERROR.getMessage(), e);
        }
    }

    /**
     * 기준점 대비 시간 가중치가 적용된 기본 점수 계산
     */
    public double calculateBaseScore() {
        long nowSeconds = System.currentTimeMillis() / 1000;
        long referenceTime = 1767225600L; // 2026-01-01
        double timeWeight = (nowSeconds - referenceTime) / 100000.0;
        return 1.0 + timeWeight;
    }

    /**
     * 개별 메뉴의 ID 변환 및 Redis 점수 업데이트 처리
     */
    public void processMenuScore(String menuIdStr, Integer aiCount, double baseScore) {
        try {
            // String -> Integer 검증
            Integer.parseInt(menuIdStr);

            double finalScore = baseScore * aiCount;

            // Redis 업데이트
            redisTemplate.opsForZSet().incrementScore(RANKING_KEY, menuIdStr, finalScore);

            log.info("[Redis Trend] 메뉴ID: {}, 반영점수: {} (AI횟수: {})",
                    menuIdStr, String.format("%.4f", finalScore), aiCount);

        } catch (NumberFormatException e) {
            log.error("[Type Error] MenuId 변환 실패: {}", menuIdStr);
        }
    }

    /**
     * 매일 새벽 3시에 실행하여 상위 1000개 이외의 저득점 데이터를 정리 (최적화 작업)
     */
    @Scheduled(cron = "0 0 3 * * *")
    public void manageRedisMemory() {
        try {
            log.info("[Scheduled] 랭킹 데이터 최적화 시작");

            // 현재 저장된 전체 키워드 개수 확인
            Long totalSize = redisTemplate.opsForZSet().zCard(RANKING_KEY);

            if (totalSize != null && totalSize > 1000) {
                // 점수가 낮은 순 (0위부터 데이터수 - 1001위까지) 삭제, 상위 1000개만 남김
                redisTemplate.opsForZSet().removeRange(RANKING_KEY, 0, totalSize - 1001);

                log.info("[Redis] 최적화 완료: {}개의 하위 데이터를 삭제하고 상위 1000개를 유지합니다.",
                        totalSize - 1000);
            }
        } catch (Exception e) {
            log.error("[Scheduled Error] 데이터 최적화 중 오류 발생: {}", e.getMessage());
        }
    }
}
