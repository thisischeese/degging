package com.degging.be.discovery.dto.response;

import lombok.AllArgsConstructor;
import lombok.Getter;
import lombok.NoArgsConstructor;

import java.util.Map;

/**
 * 탐색 탭 AI 서버 응답 DTO
 */

@Getter
@NoArgsConstructor
@AllArgsConstructor
public class AIDiscoveryResponse {
    private Map<String, Integer> cafes;
}
