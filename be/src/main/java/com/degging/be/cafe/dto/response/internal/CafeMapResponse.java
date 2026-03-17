package com.degging.be.cafe.dto.response.internal;

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

}