package com.degging.be.auth.dto.response;

import lombok.AllArgsConstructor;
import lombok.Getter;
import lombok.NoArgsConstructor;

@Getter
@NoArgsConstructor
@AllArgsConstructor
public class RefreshResponse {

    // 새롭게 발급된 accessToken
    private String accessToken;

    /**
     * 액세스 토큰으로 RefreshResponse 객체 생성
     *
     * @param accessToken 발급된 액세스 토큰
     * @return 생성된 RefreshResponse 객체
     */
    public static RefreshResponse of(String accessToken) {
        return new RefreshResponse(accessToken);
    }

}
