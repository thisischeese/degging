package com.degging.be.auth.dto.response;

import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Getter;

/**
 * 로그인 성공 시 발급되는 인증 정보 응답 객체
 */
@Getter
@Builder
@AllArgsConstructor
public class LoginResponse {

    private String accessToken;
    private String refreshToken;

    /**
     * 액세스 토큰과 리프레시 토큰을 받아 LoginResponse 객체 생성
     *
     * @param accessToken 발급된 액세스 토큰
     * @param refreshToken 발급된 리프레시 토큰
     * @return 생성된 LoginResponse 객체
     */
    public static LoginResponse of(String accessToken, String refreshToken) {
        return LoginResponse.builder()
                .accessToken(accessToken)
                .refreshToken(refreshToken)
                .build();
    }

}