package com.degging.be.discovery.dto.request;

import lombok.AllArgsConstructor;
import lombok.Getter;
import lombok.NoArgsConstructor;

import java.util.UUID;

/**
 * 탐색 탭 AI 서버 요청 DTO
 */
@Getter
@NoArgsConstructor
@AllArgsConstructor
public class AIDiscoveryRequest {
    private UUID user_id;
}
