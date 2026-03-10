package com.degging.be.review.dto.response;

import lombok.*;

/**
 * 카페 리뷰 응답 데이터를 담는 DTO
 */
@Getter
@AllArgsConstructor
@NoArgsConstructor
@Builder
public class ReviewResponseDto {
    private String content;
}
