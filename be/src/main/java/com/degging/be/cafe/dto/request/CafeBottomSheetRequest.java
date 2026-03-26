package com.degging.be.cafe.dto.request;

import lombok.Data;
import lombok.NoArgsConstructor;

import java.util.List;

/**
 * 지도 바텀시트 카페 리스트 조회 요청 DTO
 */
@Data
@NoArgsConstructor
public class CafeBottomSheetRequest {

    private Double latitude;                    // 현재 사용자의 위도

    private Double longitude;                   // 현재 사용자의 경도

    private boolean includeFranchise = false;   // 프랜차이즈 포함 여부

    private CafeBottomSheetSort sort = CafeBottomSheetSort.RECOMMEND;    // 정렬 기준

    private List<String> tags;                  // 필터링할 태그 리스트
}
