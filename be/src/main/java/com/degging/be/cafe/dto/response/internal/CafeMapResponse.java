package com.degging.be.cafe.dto.response.internal;

import com.degging.be.cafe.entity.CafeEntity;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Getter;
import lombok.NoArgsConstructor;

import java.util.UUID;

/**
 * 지도 마커 표시를 위한 카페 위치 응답 DTO
 */
@Getter
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class CafeMapResponse {

    private UUID cafeId;

    private Double latitude;    // 카페 위도

    private Double longitude;   // 카페 경도

    /**
     * CafeEntity를 CafeMapResponse DTO로 변환하는 정적 팩토리 메서드
     *
     * @param cafe 카페 엔티티
     * @return 마커 응답 DTO
     */
    public static CafeMapResponse from(CafeEntity cafe) {
        return CafeMapResponse.builder()
                .cafeId(cafe.getCafeId())
                .latitude(cafe.getLocation().getY())  // Point에서 위도(Y) 추출
                .longitude(cafe.getLocation().getX()) // Point에서 경도(X) 추출
                .build();
    }

}