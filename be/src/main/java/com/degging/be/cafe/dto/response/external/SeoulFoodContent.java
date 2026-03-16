package com.degging.be.cafe.dto.response.external;

import com.fasterxml.jackson.annotation.JsonProperty;
import lombok.Getter;
import lombok.NoArgsConstructor;

import java.util.List;

/**
 * 서울시 인허가 데이터 리스트 및 요약 정보 DTO
 */
@Getter
@NoArgsConstructor
public class SeoulFoodContent {

    @JsonProperty("list_total_count")
    private Integer listTotalCount; // 데이터의 총 개수

    @JsonProperty("row")
    private List<SeoulFoodItem> row;    // 업소의 상세 정보

}