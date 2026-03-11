package com.degging.be.cafe.dto.response;

import com.fasterxml.jackson.annotation.JsonIgnoreProperties;
import lombok.Getter;

import java.util.List;

/**
 * 업종별 상가업소 조회 API 응답 헤더 DTO
 */
@Getter
@JsonIgnoreProperties(ignoreUnknown = true)
public class StoreListInUpjongHeader {

    // 응답 설명
    private String description;

    // 컬럼 목록
    private List<String> columns;

    // 데이터 기준 연월
    private String stdrYm;

    // 응답 코드
    private String resultCode;

    // 응답 메세지
    private String resultMsg;
}