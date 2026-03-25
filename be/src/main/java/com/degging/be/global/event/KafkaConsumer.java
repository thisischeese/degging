package com.degging.be.global.event;

import com.degging.be.rank.service.RankService;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.kafka.annotation.KafkaListener;
import org.springframework.stereotype.Component;

import java.util.Map;

/**
 * 카프카에서 이벤트를 가져다 처리하는 Consumer 설정
 */
@Component
@Slf4j
@RequiredArgsConstructor
public class KafkaConsumer {
    private final RankService rankService;

    @KafkaListener(
            topics = "degging.cafe.search.events",
            groupId = "ranking-group",
            containerFactory = "kafkaListenerContainerFactory" // 아래 설정할 Factory 이름
    )
    public void consumerSearchEvent(SearchEvent event) {
        log.info("[Kafka Consumer] 메시지 수신 - 유저 검색 이벤트 처리 시작");

        // 검색한 메뉴 조회
        Map<String, Integer> extractedMenus = event.extractedMenus();
        if (extractedMenus == null || extractedMenus.isEmpty()) {
            log.warn("[Kafka Consumer] 처리할 메뉴 데이터가 없습니다.");
            return;
        }

        try {
            // 기존에 사용하던 베이스 점수 계산 (가중치 등)
            double baseScore = rankService.calculateBaseScore();

            // 메뉴별 점수 반영
            extractedMenus.forEach((menuIdStr, aiCount) ->
                    rankService.processMenuScore(menuIdStr, aiCount, baseScore)
            );

            log.info("[Kafka Consumer] 랭킹 반영 완료: {} 건", extractedMenus.size());
        } catch (Exception e) {
            log.error("[Kafka Consumer Error] 랭킹 업데이트 중 오류 발생. Event: {}, Error: {}",
                    event, e.getMessage(), e);
        }
    }
}