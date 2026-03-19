package com.degging.be.review.dto.request;

import com.degging.be.cafe.entity.CafeEntity;
import com.degging.be.review.entity.ReviewEntity;
import com.degging.be.review.entity.ReviewImageEntity;
import com.degging.be.user.entity.User;
import jakarta.validation.constraints.*;
import lombok.*;
import org.springframework.web.multipart.MultipartFile;

import java.util.List;
import java.util.UUID;

/**
 * 카페 리뷰 생성 요청 데이터를 담는 DTO
 * (텍스트 정보와 이미지 파일을 함께 포함)
 */
@Getter
@Setter
@AllArgsConstructor
@NoArgsConstructor
@Builder
public class ReviewRequest {
    private UUID cafeId;

    @Min(value = 1, message = "평점은 최소 1점 이상이어야 합니다.")
    @Max(value = 5, message = "평점은 최대 5점 이하여야 합니다.")
    private short rating; // 평점

    @NotBlank(message = "리뷰 내용은 필수입니다.")
    private String content;

    @Size(max = 3, message = "이미지는 최대 3장까지 업로드 가능합니다.")
    private List<MultipartFile> images; // 이미지

    public ReviewEntity toEntity(User loginUser, CafeEntity cafe){
        return ReviewEntity.builder()
                .cafe(cafe)
                .rating(this.getRating())
                .content(this.getContent())
                .user(loginUser)
                .build();
    }
}
