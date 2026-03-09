package com.degging.be.review.dto.request;

import jakarta.validation.constraints.Max;
import jakarta.validation.constraints.Min;
import jakarta.validation.constraints.NotBlank;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Getter;
import lombok.NoArgsConstructor;

import java.util.List;
import java.util.UUID;

/**
 * 리뷰 수정용 DTO
 */
@Getter
@AllArgsConstructor
@NoArgsConstructor
@Builder
public class ReviewUpdateRequestDto {
    @Min(1) @Max(5)
    private Short rating;

    @NotBlank
    private String content;

    private List<UUID> deleteImageIds; // 삭제할 이미지 ID
}
