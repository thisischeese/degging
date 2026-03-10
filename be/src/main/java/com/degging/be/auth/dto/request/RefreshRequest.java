package com.degging.be.auth.dto.request;

import jakarta.validation.constraints.NotBlank;
import lombok.AllArgsConstructor;
import lombok.Getter;
import lombok.NoArgsConstructor;

/**
 * Access Token 재발급 시 사용되는 데이터 객체
 */
@Getter
@NoArgsConstructor
@AllArgsConstructor
public class RefreshRequest {

    // 만료된 Access Token을 갱신하기 위한 Refresh Token
    @NotBlank(message = "리프레시 토큰은 필수입니다.")
    private String refreshToken;

}
