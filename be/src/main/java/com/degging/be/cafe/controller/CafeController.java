package com.degging.be.cafe.controller;

import com.degging.be.cafe.service.CafeCollectService;
import com.degging.be.cafe.service.CafeDuplicateService;
import com.degging.be.cafe.service.CafeStatusService;
import com.degging.be.global.dto.BaseResponse;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.web.bind.annotation.*;

/**
 * 카페 데이터 수집 및 저장을 담당하는 컨트롤러
 *
 * collect -> match -> status 순차적 실행
 */
@Slf4j
@RestController
@RequiredArgsConstructor
@RequestMapping("/api/cafes")
public class CafeController {

    private final CafeCollectService cafeCollectService;
    private final CafeDuplicateService cafeDuplicateService;
    private final CafeStatusService cafeStatusService;

    /**
     * 카페 데이터 수집
     * 
     * @return 데이터 수집 실행 성공 응답
     */
    @PostMapping("/collect")
    public BaseResponse<Void> collect() {
        log.info("소상공인 상가정보 API 데이터 수집 시작");
        cafeCollectService.collectCafes();
        return BaseResponse.success();
    }

    /**
     * 카카오 API 기반 카페 데이터 정교화
     *
     * @return 성공 응답
     */
    @PostMapping("/match")
    public BaseResponse<Void> match() {
        log.info("카카오 API 매칭 시작");
        cafeDuplicateService.matchKakaoPlaces();
        return BaseResponse.success();
    }

    /**
     * 서울시 인허가 데이터 기반 전체 카페 영업 상태 업데이트
     *
     * @return 성공 응답
     */
    @PostMapping("/status")
    public BaseResponse<Void> syncCafeStatus() {
        log.info("서울시 인허가 데이터 기반 카페 영업 상태 동기화 시작");
        cafeStatusService.syncAllCafeStatus();
        return BaseResponse.success();
    }
}