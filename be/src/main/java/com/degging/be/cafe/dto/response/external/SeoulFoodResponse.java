package com.degging.be.cafe.dto.response.external;

import com.fasterxml.jackson.annotation.JsonProperty;
import lombok.Getter;
import lombok.NoArgsConstructor;

/**
 * 서울시 인허가 API 최상위 응답 DTO
 *
 * JSON 구조:
 * {
 *  "localdata_072405": {
 *      "list_total_count": 143336,
 *      "RESULT": { ... },
 *      "row": [ ... ]
 *  }
 * }
 */
@Getter
@NoArgsConstructor
public class SeoulFoodResponse {

    @JsonProperty("localdata_072405")
    private SeoulFoodContent content;   // 인허가 정보

}