package com.degging.be.cafe.dto.request;

import lombok.Getter;
import lombok.RequiredArgsConstructor;

/**
 * 바텀시트 카페 리스트 정렬 기준 Enum
 */
@Getter
@RequiredArgsConstructor
public enum CafeBottomSheetSort {

    DISTANCE("거리순"),

    RATING("별점순"),

    REVIEW_COUNT("리뷰 많은 순"),

    RECOMMEND("추천순");

    private final String description;
}
