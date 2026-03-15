package com.degging.be.cafe.dto.response.external;

import com.fasterxml.jackson.annotation.JsonIgnoreProperties;
import lombok.Getter;

import java.util.List;

/**
 * 업종별 상가업소 조회 API 응답 바디 DTO
 */
@Getter
@JsonIgnoreProperties(ignoreUnknown = true)
public class StoreListInUpjongBody {

    // 실제 상가업소 목록
    private List<StoreListInUpjongItem> items;

    // 페이지당 조회 건수
    private Integer numOfRows;

    // 현재 페이지 번호
    private Integer pageNo;

    // 전체 건수
    private Integer totalCount;
}