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
    private String color;
    private List<ScrapCafeResponse> cafes; // 카페 정보 리스트
    private List<String> thumbnailUrls; // 썸네일용 이미지 최대 4개, 없는 경우 null 로 채움 
}
