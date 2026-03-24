package com.degging.be.cafe.entity;

import lombok.AllArgsConstructor;
import lombok.Getter;

/**
 * 카페 카테고리 분류 (커피, 제과, 디저트)
 */
@Getter
@AllArgsConstructor
public enum CafeCategory {
    COFFEE("커피"),
    BAKERY("제과/베이커리"),
    DESSERT("디저트/기타");

    private final String description;
}
