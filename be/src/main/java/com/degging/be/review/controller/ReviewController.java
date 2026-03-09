package com.degging.be.review.controller;

import com.degging.be.global.dto.BaseResponse;
import com.degging.be.review.dto.request.ReviewRequestDto;
import com.degging.be.review.dto.response.ReviewResponseDto;
import com.degging.be.review.service.ReviewService;
import jakarta.validation.Valid;
import lombok.RequiredArgsConstructor;
import org.springframework.http.MediaType;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.multipart.MultipartFile;

import java.util.List;
import java.util.UUID;

@RestController
@RequestMapping("/api/cafes")
@RequiredArgsConstructor
public class ReviewController {
    private final ReviewService reviewService;

    /**
     * 특정 카페의 리뷰를 생성하는 메서드
     * @param request (리뷰 내용을 담은 Request 객체)
     * @return 200
     */
    @PostMapping(value = "/{cafeId}/reviews", consumes = {MediaType.MULTIPART_FORM_DATA_VALUE})
    public BaseResponse<ReviewResponseDto> createReview(
                @PathVariable("cafeId") UUID cafeId,
                @Valid @RequestPart("data") ReviewRequestDto request,
                @RequestPart(value = "images", required = false) List<MultipartFile> images){
            // TODO : JWT 로그인 유저 연결 추가
        UUID loginUser = UUID.randomUUID(); // 임시
        // 등록
        reviewService.createReview(request, loginUser, images, cafeId);
        return BaseResponse.success();
    }
}
