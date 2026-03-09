package com.degging.be.review.controller;

import com.degging.be.global.dto.BaseResponse;
import com.degging.be.review.dto.request.ReviewRequestDto;
import com.degging.be.review.dto.request.ReviewUpdateRequestDto;
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
@RequestMapping("/api")
@RequiredArgsConstructor
public class ReviewController {
    private final ReviewService reviewService;

    /**
     * 특정 카페의 리뷰를 생성하는 메서드
     * @param request (리뷰 내용을 담은 Request 객체)
     * @return 200
     */
    @PostMapping(value = "/cafes/{cafeId}/reviews", consumes = {MediaType.MULTIPART_FORM_DATA_VALUE})
    public BaseResponse<ReviewResponseDto> createReview(
                @PathVariable("cafeId") UUID cafeId,
                @Valid @RequestPart("data") ReviewRequestDto request,
                @RequestPart(value = "images", required = false) List<MultipartFile> images){
            // TODO : JWT 로그인 유저 연결 추가
        UUID loginUser = UUID.fromString("45d92262-53e7-4b90-bbe5-8b216eb98cbf"); // 임시
        // 등록
        reviewService.createReview(request, loginUser, images, cafeId);
        return BaseResponse.success();
    }

    /**
     * 특정 ID 리뷰를 수정하는 메서드
     * @param reviewId
     * @param request (평점, 내용, 삭제할 사진 ID 리스트)
     * @param newImages (새로운 이미지)
     * @return 200
     */
    @PatchMapping(value = "/reviews/{reviewId}", consumes = {MediaType.MULTIPART_FORM_DATA_VALUE})
    public BaseResponse<ReviewResponseDto> updateReview(
            @PathVariable("reviewId") UUID reviewId,
            @Valid @RequestPart("data") ReviewUpdateRequestDto request,
            @RequestPart(value = "images", required = false) List<MultipartFile> newImages){
        UUID loginUser = UUID.fromString("45d92262-53e7-4b90-bbe5-8b216eb98cbf"); // 임시
        reviewService.updateReview(request, loginUser, newImages, reviewId);
        return BaseResponse.success();
    }

    /**
     * 특정 ID 리뷰를 삭제하는 메서드
     * @param reviewId
     * @return 200
     */
    @DeleteMapping(value = "/reviews/{reviewId}")
    public BaseResponse<ReviewResponseDto> deleteReview(
            @PathVariable("reviewId") UUID reviewId){
        UUID loginUser = UUID.fromString("45d92262-53e7-4b90-bbe5-8b216eb98cbf"); // 임시
        reviewService.deleteReview(reviewId, loginUser);
        return BaseResponse.success();
    }
}
