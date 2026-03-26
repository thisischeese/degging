package com.degging.be.cafe.dto.response.internal;

import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Getter;
import lombok.NoArgsConstructor;

import java.util.List;

/**
 * 지도 마커 목록을 포함하는 응답 DTO
 */
@Getter
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class CafeMapMarkersResponse {

    private List<CafeMapResponse> markers;  // 지도 마커 리스트

    public static CafeMapMarkersResponse of(List<CafeMapResponse> markers) {
        return CafeMapMarkersResponse.builder()
                .markers(markers)
                .build();
    }
}
