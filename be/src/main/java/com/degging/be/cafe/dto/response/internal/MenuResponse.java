package com.degging.be.cafe.dto.response.internal;

import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Getter;
import lombok.NoArgsConstructor;

/**
 * 특정 카페의 메뉴 정보 조회에 사용하는 응답 DTO
 */
@Getter
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class MenuResponse {

    private Long menuId;    // 메뉴 id

    private String menuName;    // 메뉴명

    private Integer price;  // 금액

    private String menuDescription; // 메뉴 설명

}