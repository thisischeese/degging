package com.degging.be.cafe.dto.response.internal;

import com.degging.be.cafe.entity.CafeEntity;
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

    /**
     * 카페 엔티티를 바탕으로 온보딩 응답 DTO 생성
     *
     * @param cafe 카페 엔티티
     * @return 변환된 온보딩 응답 DTO
     */
    public static CafeOnboardingResponse from(CafeEntity cafe) {
        return CafeOnboardingResponse.builder()
                .cafeId(cafe.getCafeId())
                .thumbnailUrl(cafe.getThumbnailUrl())
                .build();
    }

}