package com.degging.be.cafe.dto.response.external;

import com.fasterxml.jackson.annotation.JsonProperty;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Getter;
import lombok.NoArgsConstructor;

import java.util.*;

/**
 * 검색 요청 전송 후 AI 응답을 받을 DTO 
 */
@Getter
@AllArgsConstructor
@NoArgsConstructor
@Builder
public class AiSearchResponse {
    private Map<String, Integer> cafes; // AI가 추천한 카페 ID 리스트 (String 으로 받아 UUID 로 변환하여 사용)

    @JsonProperty("extracted_menus")
    private Map<String, Integer> extractedMenus; // 디저트명, 횟수

    @JsonProperty("menu_count")
    private int menuCount; // 추출된 메뉴 개수

    // 편의상 UUID 리스트만 뽑아주는 메서드
    public List<UUID> getCafeIds() {
        if (cafes == null || cafes.isEmpty()) {
            return Collections.emptyList();
        }

        // Map의 Key(UUID 문자열)들을 추출하여 UUID로 변환
        return cafes.keySet().stream()
                .map(UUID::fromString)
                .toList();
    }

    // 빈 리스트 반환하는 메서드
    public static AiSearchResponse empty() {
        return AiSearchResponse.builder()
                .cafes(Collections.emptyMap())
                .extractedMenus(Collections.emptyMap())
                .menuCount(0)
                .build();
    }
}
