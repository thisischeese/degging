package com.degging.be.cafe.dto.request;

import com.fasterxml.jackson.annotation.JsonProperty;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Getter;
import lombok.NoArgsConstructor;

import java.util.Collections;
import java.util.List;
import java.util.UUID;

/**
 * AI 서버로 요청을 보낼 때 사용하는 DTO
 */
@Getter
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class AiSearchRequest {
    // AI 서버가 받는 필드명과 맞춰줌
    @JsonProperty("mood")
    private List<UUID> mood; // 분위기 태그

    @JsonProperty("userId") // 카멜로 보내야함
    private UUID userId; 

    private String keyword; // 사용자 입력 검색어

    private Double latitude;
    private Double longitude;

    // 데이터를 조합해 AI 요청 DTO 를 생성하는 메서드
    public static AiSearchRequest of(UUID userId, CafeSearchRequest request, List<UUID> tagIds){
        return AiSearchRequest.builder()
                .userId(userId)
                .mood(tagIds)
                .keyword(request.getKeyword())
                .longitude(request.getLongitude())
                .latitude(request.getLatitude())
                .build();
    }
}
