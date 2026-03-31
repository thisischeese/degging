package com.degging.be.infra.external.dto.response;

import com.fasterxml.jackson.annotation.JsonIgnoreProperties;
import com.fasterxml.jackson.annotation.JsonProperty;
import lombok.Getter;
import lombok.NoArgsConstructor;

/**
 * 서울시 인허가 개별 업소 정보 DTO
 */
@Getter
@NoArgsConstructor
@JsonIgnoreProperties(ignoreUnknown = true)
public class SeoulFoodItem {

    @JsonProperty("BPLCNM")
    private String bplcNm;      // 사업장명

    @JsonProperty("TRDSTATENM")
    private String trdStateNm;  // 영업상태명 (영업/정상, 폐업 등)

    @JsonProperty("SITEWHLADDR")
    private String siteWhlAddr; // 지번주소

    @JsonProperty("RDNWHLADDR")
    private String rdnWhlAddr;  // 도로명주소

    @JsonProperty("UPTAENM")
    private String uptaeNm;     // 업태명 (커피숍, 기타 휴게음식점 등)

}