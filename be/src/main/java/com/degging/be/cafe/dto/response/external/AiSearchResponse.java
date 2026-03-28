package com.degging.be.cafe.dto.response.external;

import com.fasterxml.jackson.annotation.JsonIgnoreProperties;
import com.fasterxml.jackson.annotation.JsonProperty;
import lombok.*;

import java.util.*;

/**
 * 검색 요청 전송 후 AI 응답을 받을 DTO
 */
@Getter
@Setter // Jackson이 값을 채울 때 필요
@NoArgsConstructor
@AllArgsConstructor
@Builder
@JsonIgnoreProperties(ignoreUnknown = true) // 파싱 오류 무시
public class AiSearchResponse {

    /**
     * AI 응답: { "cafe_id": 1, "cafe_id": 2 }
     * Key: UUID(String), Value: 순위(Integer) - 무조건 정수 응답 대응
     */
    private Map<String, Integer> cafes;

    /**
     * AI 응답: ["두쫀쿠", "버터떡", "두쫀쿠"]
     * 단순 리스트이므로 List<String>으로 변경
     */
    @JsonProperty("extracted_menus")
    private List<String> extractedMenus;

    // 서비스 로직에서 UUID 리스트를 편하게 뽑기 위한 메서드
    public List<UUID> getCafeIds() {
        if (cafes == null || cafes.isEmpty()) {
            return Collections.emptyList();
        }
        // Map의 Key들만 모아서 UUID로 변환
        return cafes.keySet().stream()
                .map(UUID::fromString)
                .toList();
    }

    // 서비스 정렬 로직에서 사용할 순위 반환 메서드
    public Integer getCafeRank(String cafeId) {
        if (cafes == null || cafes.get(cafeId) == null) {
            return 999; // 순위 정보가 없으면 가장 뒤로
        }
        return cafes.get(cafeId);
    }

    public static AiSearchResponse empty() {
        return AiSearchResponse.builder()
                .cafes(Collections.emptyMap())
                .extractedMenus(Collections.emptyList())
                .build();
    }
}