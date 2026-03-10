package com.degging.be.review.dto.request;

import jakarta.validation.constraints.Max;
import jakarta.validation.constraints.Min;
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.Size;
import lombok.*;
import org.springframework.web.multipart.MultipartFile;

import java.util.List;
import java.util.UUID;

/**
 * 리뷰 수정용 DTO
 */
@Getter
@Setter
@AllArgsConstructor
@NoArgsConstructor
@Builder
public class ReviewUpdateRequest {
    @Min(1) @Max(5)
    private Short rating;

    @NotBlank
    private String content;

    private List<UUID> deleteImageIds; // 삭제할 이미지 ID

    // 새로 추가하려는 이미지 파일들
    @Size(max = 3, message = "이미지는 최대 3장까지 가능합니다.")
    private List<MultipartFile> images;
}
