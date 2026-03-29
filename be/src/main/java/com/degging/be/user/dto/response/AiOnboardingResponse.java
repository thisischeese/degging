package com.degging.be.user.dto.response;

import lombok.AllArgsConstructor;
import lombok.Getter;
import lombok.NoArgsConstructor;

import java.time.LocalDateTime;
import java.util.UUID;

/**
 * AI 서버 온보딩 응답 DTO
 */
@Getter
@NoArgsConstructor
@AllArgsConstructor
public class AiOnboardingResponse {

    private String status;

    private String message;

    private Data data;

    @Getter
    @NoArgsConstructor
    @AllArgsConstructor
    public static class Data {
        private UUID user_id;
        private LocalDateTime updated_at;
    }

    public boolean isSuccess() {
        return "success".equalsIgnoreCase(this.status);
    }
}
