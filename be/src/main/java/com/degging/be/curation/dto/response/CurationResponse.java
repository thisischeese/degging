package com.degging.be.curation.dto.response;

import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Getter;
import lombok.NoArgsConstructor;

import java.util.List;

/**
 * 큐레이션 카페 리스트 응답 DTO
 */

@Getter
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class CurationResponse {

    private List<CurationCafeResponse> cafeList;

    public static CurationResponse of(List<CurationCafeResponse> cafeList) {
        return CurationResponse.builder()
                .cafeList(cafeList)
                .build();
    }
}
