package com.degging.be.cafe.dto.request;

import com.degging.be.cafe.entity.CafeEntity;
import com.fasterxml.jackson.annotation.JsonProperty;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Getter;
import lombok.NoArgsConstructor;

import java.util.UUID;

/**
 * AI 서버(크롤러)에 크롤링 요청 시 전송하는 카페 기본 정보 DTO
 */
@Getter
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class AiCrawlerRequestDto {

    @JsonProperty("cafe_id")
    private UUID cafeId;

    private String name;

    /**
     * CafeEntity에서 크롤러 요청 DTO 생성
     *
     * @param cafe 카페 엔티티
     * @return AI 크롤러 요청 DTO
     */
    public static AiCrawlerRequestDto from(CafeEntity cafe) {
        return AiCrawlerRequestDto.builder()
                .cafeId(cafe.getCafeId())
                .name(cafe.getName())
                .build();
    }
}
