package com.degging.be.cafe.entity;

import lombok.AllArgsConstructor;
import lombok.Getter;

/**
 * 카페의 영업/폐업 여부 확인을 위한 Enum
 */
@Getter
@AllArgsConstructor
public enum CafeStatus {
    OPEN("영업중"),
    CLOSED("폐업"),
    UNKNOWN("상태 확인 불가");

    private final String description;
}
