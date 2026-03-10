package com.degging.be.user.entity;

import lombok.AllArgsConstructor;
import lombok.Getter;

/**
 * 사용자 성별을 나타내는 Enum
 */
@Getter
@AllArgsConstructor
public enum Gender {
    MALE("남성"),
    FEMALE("여성");

    private String description;
}
