package com.degging.be.review.dto.request;

import lombok.*;
import org.springframework.web.multipart.MultipartFile;

import java.util.List;
import java.util.UUID;

@Getter
@AllArgsConstructor
@NoArgsConstructor
@Builder
public class ReviewRequestDto {
    private UUID cafeId;
    private int rating; // 평점
    private String content;
    private List<MultipartFile> images; // 이미지
}
