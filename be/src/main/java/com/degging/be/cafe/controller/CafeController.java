package com.degging.be.cafe.controller;

import com.degging.be.cafe.service.CafeCollectService;
import com.degging.be.cafe.service.CafeDuplicateService;
import com.degging.be.global.dto.BaseResponse;
import lombok.RequiredArgsConstructor;
import org.springframework.web.bind.annotation.*;

/**
 * 카페 데이터 수집 및 저장을 담당하는 컨트롤러
 */
@RestController
@RequiredArgsConstructor
@RequestMapping("/api/cafes")
public class CafeController {

    private final CafeCollectService cafeCollectService;
    private final CafeDuplicateService cafeDuplicateService;

    /**
     * 카페 데이터 수집
     * 
     * @return 데이터 수집 실행 성공 응답
     */
    @PostMapping("/collect")
    public BaseResponse<Void> collect() {
        cafeCollectService.collectCafes();
        return BaseResponse.success();
    }

    /**
     * 카카오 API 기반 카페 데이터 정교화
     */
    @PostMapping("/match")
    public BaseResponse<Void> match() {
        cafeDuplicateService.matchKakaoPlaces();
        return BaseResponse.success();
    }
}