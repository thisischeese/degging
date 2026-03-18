package com.degging.be.cafe.dto.response.internal;

import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Getter;
import lombok.NoArgsConstructor;

import java.util.UUID;

/**
 * 카페 상세 정보 조회에 사용하는 응답 DTO
 */
@Getter
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class CafeOnboardingResponse {

    // 카페 고유 식별자
    private UUID cafeId;

    // 카페 대표 이미지 URL
    private String thumbnailUrl;

}