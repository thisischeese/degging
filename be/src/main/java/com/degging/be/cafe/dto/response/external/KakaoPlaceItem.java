package com.degging.be.cafe.dto.response.external;

import com.fasterxml.jackson.annotation.JsonIgnoreProperties;
import com.fasterxml.jackson.databind.PropertyNamingStrategies;
import com.fasterxml.jackson.databind.annotation.JsonNaming;
import lombok.Getter;

/**
 * 카카오 장소 검색 API의 개별 장소 정보 DTO
 *
 * 카카오 API의 JSON 응답 중 documents 배열 내부 객체 매핑
 */
@Getter
@JsonIgnoreProperties(ignoreUnknown = true)
@JsonNaming(PropertyNamingStrategies.SnakeCaseStrategy.class)
public class KakaoPlaceItem {

    private String id;  // 카카오 플레이스 id

    private String placeName;   // 업소명

    private String categoryName; // 카테고리 이름 (ex. 음식점 > 카페 > 커피전문점)

    private String categoryGroupCode; // 카테고리 그룹 코드 (CE7: 카페)

    private String addressName; // 지번주소

    private String roadAddressName; // 도로명주소

    private String phone;   // 전화번호
    
    private String x;       // 경도 (longitude)
    
    private String y;       // 위도 (latitude)

    private String placeUrl;    // 카카오맵 url
}