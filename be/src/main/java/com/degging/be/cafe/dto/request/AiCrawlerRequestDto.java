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

    private UUID cafeId;

    private String name;

    /**
     * CafeEntity에서 크롤러 요청 DTO 생성
     *
     * @param cafe 카페 엔티티
     * @return AI 크롤러 요청 DTO
     */
    public static AiCrawlerRequestDto from(CafeEntity cafe) {
        String requestName = cafe.getName();

        // 크롤링 서버 요청 시 명칭 매핑 (검색 성능 향상을 위해)
        if ("미니마이즈".equals(requestName)) {
            requestName = "미니마이즈 이태원점";
        } else if ("아삐뽀레 익선점".equals(requestName)) {
            requestName = "아삐뽀레";
        }

        return AiCrawlerRequestDto.builder()
                .cafeId(cafe.getCafeId())
                .name(requestName)
                .build();
    }
}
