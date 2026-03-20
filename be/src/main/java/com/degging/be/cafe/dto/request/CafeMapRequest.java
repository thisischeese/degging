package com.degging.be.cafe.dto.request;

import lombok.Getter;
import lombok.NoArgsConstructor;

/**
 * 사용자 위치 기반 반경 조회를 위한 요청 DTO
 */
@Getter
@NoArgsConstructor
public class CafeMapRequest {
    private Double latitude;                    // 현재 사용자의 위도
    private Double longitude;                   // 현재 사용자의 경도
    private boolean includeFranchise = false;   // 프랜차이즈 포함 여부
}