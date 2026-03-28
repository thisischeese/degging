package com.degging.be.cafe.dto.response.external;

import com.fasterxml.jackson.annotation.JsonProperty;
import com.fasterxml.jackson.annotation.JsonSetter;
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

    // cafes로 오든, top_cafe_ids로 오든 이 메서드로 처리 가능
    @JsonSetter(value = "cafes")
    @JsonProperty("top_cafe_ids")
    public void setCafes(Object cafes) {
        if (cafes instanceof List<?> list) {
            // List로 올 때: ["uuid1", "uuid2"] -> Map에 순서대로 담기
            this.cafes = new LinkedHashMap<>(); // 순서 유지를 위해 LinkedHashMap 사용
            for (int i = 0; i < list.size(); i++) {
                Object item = list.get(i);
                if (item != null) {
                    this.cafes.put(item.toString(), i + 1);
                }
            }
        } else if (cafes instanceof Map<?, ?> map) {
            // Map으로 올 때: {"uuid1": 1, "uuid2": 2} -> 그대로 캐스팅
            // Key는 String(UUID), Value는 Integer(순위)
            this.cafes = new LinkedHashMap<>();
            map.forEach((k, v) -> {
                if (k != null && v != null) {
                    this.cafes.put(k.toString(), Integer.parseInt(v.toString()));
                }
            });
        }
    }

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
