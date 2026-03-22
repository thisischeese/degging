package com.degging.be.cafe.dto.response.external;

import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Getter;
import lombok.NoArgsConstructor;

import java.util.List;
import java.util.UUID;

/**
 * 검색 요청 전송 후 AI 응답을 받을 DTO 
 * TODO : 임시라서 상의 후 규격 형식 맞춰 변경 필요
 */
@Getter
@AllArgsConstructor
@NoArgsConstructor
@Builder
public class AiSearchResponse {
    private String status;           // AI 처리 상태
    private List<UUID> cafeIds;      // AI가 추천한 카페 ID 리스트
    private String aiLogId;          // AI 서버측 로그 ID (디버깅용)
}
