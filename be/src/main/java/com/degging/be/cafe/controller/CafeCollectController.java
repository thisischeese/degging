package com.degging.be.cafe.controller;

import com.degging.be.cafe.service.CafeCollectService;
import com.degging.be.global.dto.BaseResponse;
import lombok.RequiredArgsConstructor;
import org.springframework.web.bind.annotation.*;

/**
 * 카페 데이터 수집 실행용 컨트롤러
 */
@RestController
@RequiredArgsConstructor
@RequestMapping("/api/cafes")
public class CafeCollectController {

    private final CafeCollectService cafeCollectService;

    /**
     * 카페 데이터 수집
     * 
     * @return 데이터 수집 실행 성공 응답
     */
    @PostMapping("/collect")
    public BaseResponse<Integer> collect() {
        cafeCollectService.collectCafes();
        return BaseResponse.success();
    }
}