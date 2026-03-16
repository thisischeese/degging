package com.degging.be.scrap.dto.response;

import com.degging.be.scrap.entity.ScrapEntity;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Getter;
import lombok.NoArgsConstructor;

import java.util.List;
import java.util.UUID;

/**
 * 스크랩 요청에 대한 응답 DTO
 */
@Getter
@NoArgsConstructor
@AllArgsConstructor
@Builder
public class ScrapResponse {
    private UUID scrapId;
    private String name;
    private List<String> thumbnailUrls; // 최대 4개의 이미지 예상
    private String color;

    // Entity -> Dto
    public static ScrapResponse toDto(ScrapEntity entity){
        return ScrapResponse.builder()
                .scrapId(entity.getScrapId())
                .name(entity.getName())
                .thumbnailUrls(entity.getThumbnailUrls())
                .color(entity.getColor())
                .build();
    }
}
