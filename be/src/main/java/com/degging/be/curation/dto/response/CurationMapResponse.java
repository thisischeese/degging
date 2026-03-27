package com.degging.be.curation.dto.response;

import com.degging.be.cafe.entity.CafeEntity;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Getter;
import lombok.NoArgsConstructor;

import java.util.UUID;

/**
 * 큐레이션 미니맵용 위치 정보 응답 DTO
 */

@Getter
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class CurationMapResponse {

    private UUID cafeId;
    private String name;
    private Double latitude;
    private Double longitude;

    public static CurationMapResponse from(CafeEntity cafe) {
        return CurationMapResponse.builder()
                .cafeId(cafe.getCafeId())
                .name(cafe.getName())
                .latitude(cafe.getLocation().getY())
                .longitude(cafe.getLocation().getX())
                .build();
    }
}
