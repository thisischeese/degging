package com.degging.be.cafe.dto.response.internal;

import com.degging.be.cafe.entity.CafeEntity;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Getter;
import lombok.NoArgsConstructor;

import java.util.UUID;

/**
 * 지도 바텀시트 카페 요약 정보 응답 DTO
 *
 * 썸네일, 카페명, 한줄 소개, 도로명 주소, 좌표를 포함합니다.
 */
@Getter
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class CafeBottomSheetResponse {

    private UUID cafeId;

    private String thumbnailUrl;    // 썸네일 이미지 URL

    private String name;            // 카페명

    private String cafeIntro;       // 한줄 소개

    private String roadAddress;     // 도로명 주소

    private Double latitude;        // 위도

    private Double longitude;       // 경도

    /**
     * CafeEntity를 CafeBottomSheetResponse DTO로 변환하는 정적 팩토리 메서드
     *
     * @param cafe 카페 엔티티
     * @return 바텀시트 응답 DTO
     */
    public static CafeBottomSheetResponse from(CafeEntity cafe) {
        return CafeBottomSheetResponse.builder()
                .cafeId(cafe.getCafeId())
                .thumbnailUrl(cafe.getThumbnailUrl())
                .name(cafe.getName())
                .cafeIntro(cafe.getCafeIntro())
                .roadAddress(cafe.getRoadAddress())
                .latitude(cafe.getLocation().getY())
                .longitude(cafe.getLocation().getX())
                .build();
    }
}
