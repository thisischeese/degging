package com.degging.be.rank.dto.response;

import lombok.*;

import java.util.List;

/**
 * 실시간 디저트 순위 조회에 대한 응답을 위한 DTO
 */
@Getter
@AllArgsConstructor
@NoArgsConstructor
@Builder
public class RankOnboardingResponse {
    private List<String> menuNames; // 디저트명 (ex 두쫀쿠, 강남역 크로플)
}
