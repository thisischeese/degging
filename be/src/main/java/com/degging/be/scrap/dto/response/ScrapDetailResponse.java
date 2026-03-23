package com.degging.be.scrap.dto.response;

import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Getter;
import lombok.NoArgsConstructor;

import java.util.List;
import java.util.UUID;

/**
 * 스크랩 상세조회 시 응답에 사용하는 DTO (카페 정보 등 포함)
 */
@Getter
@NoArgsConstructor
@AllArgsConstructor
@Builder
public class ScrapDetailResponse {
    private UUID scrapId;
    private String name;
    private List<ScrapCafeResponse> cafes; // 카페 정보 리스트
}
