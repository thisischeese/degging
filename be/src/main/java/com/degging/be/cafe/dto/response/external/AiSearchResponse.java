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
    private Object cafes; // 어떻게 들어오든 일단 받기 위함

    @JsonProperty("extracted_menus")
    private Map<String, Integer> extractedMenus;

    @JsonProperty("menu_count")
    private int menuCount;

    // 실제로 우리가 로직에서 쓸 '진짜' 데이터 보관소
    @Builder.Default
    private Map<String, Integer> cafeMap = new LinkedHashMap<>();

    // Jackson이 JSON을 읽을 때 이 메서드를 강제로 실행하게 합니다.
    @JsonSetter(value = "cafes")
    @JsonProperty("top_cafe_ids")
    public void setCafes(Object input) {
        this.cafes = input; // 원본 데이터 보관

        if (input instanceof List<?> list) {
            // AI가 []로 던졌을 때: 리스트를 돌면서 맵에 채워넣음
            this.cafeMap = new LinkedHashMap<>();
            for (int i = 0; i < list.size(); i++) {
                if (list.get(i) != null) {
                    this.cafeMap.put(list.get(i).toString(), i + 1);
                }
            }
        } else if (input instanceof Map<?, ?> map) {
            // AI가 {}로 던졌을 때: 그대로 복사
            this.cafeMap = new LinkedHashMap<>();
            map.forEach((k, v) -> {
                if (k != null && v != null) {
                    this.cafeMap.put(k.toString(), Integer.parseInt(v.toString()));
                }
            });
        }
    }

    // 서비스 레이어에서는 이 메서드만 씁니다.
    public List<UUID> getCafeIds() {
        if (cafeMap == null || cafeMap.isEmpty()) {
            return Collections.emptyList();
        }
        return cafeMap.keySet().stream()
                .map(UUID::fromString)
                .toList();
    }

    public static AiSearchResponse empty() {
        return AiSearchResponse.builder()
                .cafeMap(Collections.emptyMap())
                .extractedMenus(Collections.emptyMap())
                .menuCount(0)
                .build();
    }
}
