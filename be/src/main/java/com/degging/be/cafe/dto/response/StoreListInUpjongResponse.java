package com.degging.be.cafe.dto.response;

import com.fasterxml.jackson.annotation.JsonIgnoreProperties;
import lombok.Getter;

/**
 * 업종별 상가업소 조회 API 최상위 응답 DTO
 *
 * JSON 구조:
 * {
 *   "header": { ... },
 *   "body": { ... }
 * }
 */
@Getter
@JsonIgnoreProperties(ignoreUnknown = true)
public class StoreListInUpjongResponse {

    // 응답 헤더 정보
    private StoreListInUpjongHeader header;

    // 응답 바디 정보
    private StoreListInUpjongBody body;
}