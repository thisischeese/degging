package com.degging.be.cafe.controller;

import com.degging.be.cafe.service.CafeCollectService;
import com.degging.be.cafe.service.CafeStatusService;
import com.degging.be.global.dto.BaseResponse;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.web.bind.annotation.*;

import com.degging.be.cafe.service.CafeCrawlingService;

/**
 * 카페 데이터 관리 및 외부 수집 전용 컨트롤러
 */
@Slf4j
@RestController
@RequiredArgsConstructor
@RequestMapping("/api/manage/cafes")
public class CafeManageController {

    private final CafeCollectService cafeCollectService;
    private final CafeStatusService cafeStatusService;
    private final CafeCrawlingService cafeCrawlingService;

    /**
     * 카페 데이터 통합 수집 (공공데이터 + 카카오 매칭)
     * 
     * @return 데이터 수집 실행 성공 응답
     */
    @PostMapping("/collect")
    public BaseResponse<Void> collect() {
        log.info("통합 카페 데이터 수집 시작");
        cafeCollectService.collectCafes();
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

    /**
     * AI 크롤링 서비스 실행
     * 아직 상세 정보(썸네일 등)가 없는 카페들을 대상으로 AI 크롤링을 수행합니다.
     *
     * @return 실행 성공 응답 (비동기로 동작)
     */
    @PostMapping("/crawling")
    public BaseResponse<Void> crawling() {
        log.info("AI 크롤링 실행 요청 수신");
        cafeCrawlingService.crawling();
        return BaseResponse.success();
    }
}