package com.degging.be.global.event;

import java.time.LocalDateTime;
import java.util.List;
import java.util.UUID;

/**
 * Kafka를 통해 전송될 검색 로그 이벤트
 */
public record SearchEvent(
        List<String> extractedMenus, // 검색어에서 추출한 디저트명과 빈도
        UUID userId, // 검색한 유저 ID
        LocalDateTime timestamp // 이벤트 발생 시간
) {
    // 이벤트 발행 시간을 담아 발행
    public static SearchEvent of(List<String> extractedMenus, UUID userId){
        return new SearchEvent(extractedMenus, userId, LocalDateTime.now());
    }
}
