package com.degging.be.curation.dto.response;

import com.degging.be.cafe.entity.CafeEntity;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Getter;
import lombok.NoArgsConstructor;

import java.util.UUID;

/**
 * 큐레이션 카페 리스트 응답 DTO
 */

@Getter
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class CurationCafeResponse {

    private UUID cafeId;
    private String thumbnailUrl;
    private String name;
    private String cafeIntro;
    private String roadAddress;

    public static CurationCafeResponse from(CafeEntity cafe) {
        return CurationCafeResponse.builder()
                .cafeId(cafe.getCafeId())
                .thumbnailUrl(cafe.getThumbnailUrl())
                .name(cafe.getName())
                .cafeIntro(cafe.getCafeIntro())
                .roadAddress(cafe.getRoadAddress())
                .build();
    }
}
