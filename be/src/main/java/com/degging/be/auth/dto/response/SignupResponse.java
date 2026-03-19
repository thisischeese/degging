package com.degging.be.auth.dto.response;

import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Getter;

/**
 * 회원가입 성공 후 온보딩 진행을 위한 임시 토큰 응답 DTO
 */
@Getter
@Builder
@AllArgsConstructor
public class SignupResponse {

    // 온보딩 단계에서만 유효한 임시 액세스 토큰
    private String onboardingToken;
}