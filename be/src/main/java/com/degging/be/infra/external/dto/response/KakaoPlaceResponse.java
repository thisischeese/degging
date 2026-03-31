package com.degging.be.infra.external.dto.response;

import com.fasterxml.jackson.annotation.JsonIgnoreProperties;
import lombok.Getter;

import java.util.List;

/**
 * 카카오 장소 검색 API 응답 DTO
 *
 * JSON 구조:
 *
 * {
 *   "documents": [ ... ],
 *   "meta": { ... }
 * }
 */
@Getter
@JsonIgnoreProperties(ignoreUnknown = true)
public class KakaoPlaceResponse {

    private List<KakaoPlaceItem> documents; // 장소 검색 결과 목록
}