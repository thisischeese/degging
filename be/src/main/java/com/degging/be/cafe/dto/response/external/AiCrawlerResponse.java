package com.degging.be.cafe.dto.response.external;

import com.fasterxml.jackson.annotation.JsonProperty;
import lombok.AllArgsConstructor;
import lombok.Getter;
import lombok.NoArgsConstructor;

import java.util.List;
import java.util.UUID;

/**
 * AI 서버(크롤러)로부터 수신하는 크롤링 결과 응답 DTO
 *
 * 응답 예시:
 * {
 *   "items": [ { ... }, { ... } ],
 *   "total": 100,
 *   "missing_cafe_ids": [ "uuid1", "uuid2" ]
 * }
 */
@Getter
@NoArgsConstructor
@AllArgsConstructor
public class AiCrawlerResponse {

    /** 크롤링된 카페 상세 정보 리스트 */
    private List<AiCrawlerItemResponse> items;

    /** 이번 배치에서 실제로 크롤링된 카페 수 */
    private int total;

    /** 크롤링 실패 또는 매칭 불가 카페 ID 목록 */
    @JsonProperty("missing_cafe_ids")
    private List<UUID> missingCafeIds;
}
