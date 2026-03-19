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

    /**
     * 온보딩 토큰을 받아 응답 객체를 생성하는 정적 팩토리 메서드
     *
     * @param onboardingToken 발급된 임시 토큰
     * @return SignupResponse 객체
     */
    public static SignupResponse from(String onboardingToken) {
        return SignupResponse.builder()
                .onboardingToken(onboardingToken)
                .build();
    }

}