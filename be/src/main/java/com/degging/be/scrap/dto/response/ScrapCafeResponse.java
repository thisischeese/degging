package com.degging.be.scrap.dto.response;

import com.degging.be.scrap.entity.ScrapEntity;
import com.degging.be.scrap.entity.ScrapItemEntity;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Getter;
import lombok.NoArgsConstructor;

import java.util.List;
import java.util.UUID;

/**
 * 스크랩 상세 정보 조회에서 사용할 카페 정보 DTO
 */
@Getter
@Builder
@AllArgsConstructor
@NoArgsConstructor
public class ScrapCafeResponse {
    private UUID cafeId;
    private String name;
    private String cafeIntro; // 필요한 정보만 골라서 정의

    public static ScrapCafeResponse toDto(ScrapItemEntity scrap){
        return ScrapCafeResponse.builder()
                        .cafeId(scrap.getCafe().getCafeId()) // 빈값
                        .name(scrap.getCafe().getName())
                        .cafeIntro(scrap.getCafe().getCafeIntro())
                        .build();
    }
}
