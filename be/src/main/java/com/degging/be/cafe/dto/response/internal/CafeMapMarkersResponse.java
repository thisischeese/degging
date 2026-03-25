package com.degging.be.cafe.dto.response.internal;

import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Getter;
import lombok.NoArgsConstructor;

import java.util.List;

/**
 * 지도 마커와 현재 적용된 필터 태그를 포함하는 응답 DTO
 */
@Getter
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class CafeMapMarkersResponse {

    private List<CafeMapResponse> markers;  // 지도 마커 리스트

    private List<String> filterTags;        // 현재 적용된 필터 태그 (사용자 취향 또는 수동 선택)

    public static CafeMapMarkersResponse of(List<CafeMapResponse> markers, List<String> filterTags) {
        return CafeMapMarkersResponse.builder()
                .markers(markers)
                .filterTags(filterTags)
                .build();
    }
}
