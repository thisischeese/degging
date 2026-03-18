package com.degging.be.rank.controller;

import com.degging.be.global.dto.BaseResponse;
import com.degging.be.rank.dto.response.RankResponse;
import com.degging.be.rank.service.RankService;
import lombok.RequiredArgsConstructor;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

/**
 * 실시간 디저트 순위를 관리하는 API 컨트롤러
 */
@RestController
@RequestMapping("/api/ranks")
@RequiredArgsConstructor
public class RankController {
    private final RankService rankService;

    // 확장성 고려하여 변수로 선언
    private static final int DEFAULT_RANK_COUNT = 5;
    private static final int ONBOARDING_RANK_COUNT = 20;

    /**
     * 실시간 디저트 랭킹(트렌드) 상위 5개를 조회합니다.
     * Redis 에 누적된 키워드 점수를 내림차순으로 반환합니다.
     * @return 200 (OK)
     * 상위 5개의 순위 및 키워드 목록(RankResponse)
     */
    @GetMapping("/desserts")
    public BaseResponse<RankResponse> getTop5(){
        RankResponse result = rankService.getTopRanks(DEFAULT_RANK_COUNT);
        return BaseResponse.success(result);
    }

    /**
     * 실시간 디저트 랭킹(트렌드) 상위 20개를 조회합니다.
     * Redis 에 누적된 키워드 점수를 내림차순으로 반환합니다.
     * @return 200 (OK), 상위 20개의 순위 및 키워드 목록(RankResponse)
     */
    @GetMapping("/desserts/onboarding")
    public BaseResponse<RankResponse> getTop20ForOnboarding(){
        RankResponse result = rankService.getTopRanks(ONBOARDING_RANK_COUNT);
        return BaseResponse.success(result);
    }
}
