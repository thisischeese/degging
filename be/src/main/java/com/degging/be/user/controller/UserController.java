package com.degging.be.user.controller;

import com.degging.be.global.dto.BaseResponse;
import com.degging.be.user.dto.request.UserOnboardingRequest;
import jakarta.validation.Valid;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.web.bind.annotation.*;

import java.util.UUID;

@Slf4j
@RestController
@RequiredArgsConstructor
@RequestMapping("/api/users")
public class UserController {

    /**
     * 유저의 온보딩 선택 결과를 수집합니다.
     *
     * @param request 선택한 카페 및 디저트 ID 리스트
     * @return 수집 성공 여부 응답
     */
    @PostMapping("/onboarding")
    public BaseResponse<String> collectOnboarding(
            @Valid @RequestBody UserOnboardingRequest request) {

        // TODO: 토큰 검증 및 유저 취향 분석 로직 연동 예정
        log.info("온보딩 토큰 {}에 대한 데이터 수집 시도", request.getOnboardingToken());

        return BaseResponse.success("온보딩 정보가 성공적으로 수신되었습니다.");
    }

}