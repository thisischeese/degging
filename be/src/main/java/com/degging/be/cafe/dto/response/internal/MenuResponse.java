package com.degging.be.cafe.dto.response.internal;

import com.degging.be.cafe.entity.CafeMenuEntity;
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

    private String menuImageUrl;    // 메뉴 이미지 URL

    private Integer price;  // 금액

    private String menuDescription; // 메뉴 설명

    /**
     * 메뉴 엔티티를 메뉴 응답 DTO로 변환
     *
     * @param entity 카페 메뉴 엔티티
     * @return  가공된 메뉴 응답 DTO
     */
    public static MenuResponse from(CafeMenuEntity entity) {
        return MenuResponse.builder()
                .menuId(entity.getMenuId())
                .menuName(entity.getMenuName())
                .menuImageUrl(entity.getMenuImageUrl())
                .price(entity.getPrice())
                .menuDescription(entity.getMenuDescription())
                .build();
    }

}