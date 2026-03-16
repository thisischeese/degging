package com.degging.be.cafe.dto.response;

import com.fasterxml.jackson.annotation.JsonIgnoreProperties;
import lombok.Getter;

/**
 * 카카오 장소 검색 API의 개별 장소 정보 DTO
 *
 * 카카오 API의 JSON 응답 중 documents 배열 내부 객체 매핑
 */
@Getter
@JsonIgnoreProperties(ignoreUnknown = true)
public class KakaoPlaceItem {

    private String id;  // 카카오 플레이스 id

    private String placeName;   // 업소명

    private String addressName; // 지번주소

    private String roadAddressName; // 도로명주소

    private String phone;   // 전화번호

    private String placeUrl;    // 카카오맵 url
}