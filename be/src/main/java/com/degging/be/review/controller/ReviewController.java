package com.degging.be.review.controller;

import com.degging.be.global.dto.BaseResponse;
import com.degging.be.global.exception.BaseException;
import com.degging.be.global.exception.errorcode.CommonErrorCode;
import com.degging.be.review.dto.request.ReviewRequest;
import com.degging.be.review.dto.request.ReviewUpdateRequest;
import com.degging.be.review.dto.response.ReviewResponseDto;
import com.degging.be.review.service.ReviewService;
import jakarta.validation.Valid;
import lombok.RequiredArgsConstructor;
import org.springframework.http.MediaType;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.multipart.MultipartFile;
import org.springframework.security.core.annotation.AuthenticationPrincipal;
import org.springframework.security.core.userdetails.UserDetails;

import java.util.List;
import java.util.UUID;

@RestController
@RequestMapping("/api")
@RequiredArgsConstructor
public class ReviewController {
    private final ReviewService reviewService;

    private UUID getUserId(UserDetails user) {
        if (user == null) {
            throw new BaseException(CommonErrorCode.UNAUTHORIZED);
        }
        return UUID.fromString(user.getUsername());
    }
    /**
     * 특정 카페의 리뷰를 생성하는 메서드
     * @param request (리뷰 내용을 담은 Request 객체)
     * @return 200
     */
    @PostMapping(value = "/cafes/{cafeId}/reviews", consumes = {MediaType.MULTIPART_FORM_DATA_VALUE})
    public BaseResponse<ReviewResponseDto> createReview(
                    @PathVariable("cafeId") UUID cafeId,
                    @ModelAttribute @Valid ReviewRequest request,
                    @AuthenticationPrincipal UserDetails user){
        UUID userId = getUserId(user);
        // 관심사 분리를 위해 알맞게 나눠담아 호출
        List<MultipartFile> images = request.getImages(); 
        reviewService.createReview(request, userId, images, cafeId);
        return BaseResponse.success();
    }

    /**
     * 특정 ID 리뷰를 수정하는 메서드
     * @param reviewId
     * @param request (평점, 내용, 삭제할 사진 ID 리스트, 새로 추가한 사진 리스트)
     * @return 200
     */
    @PatchMapping(value = "/reviews/{reviewId}", consumes = {MediaType.MULTIPART_FORM_DATA_VALUE})
    public BaseResponse<ReviewResponseDto> updateReview(
                    @PathVariable("reviewId") UUID reviewId,
                    @Valid @ModelAttribute("data") ReviewUpdateRequest request,
                    @AuthenticationPrincipal UserDetails user){
        UUID userId = getUserId(user);
        List<MultipartFile> newImages = request.getImages();
        reviewService.updateReview(request, userId, newImages, reviewId);
        return BaseResponse.success();
    }

    /**
     * 특정 ID 리뷰를 삭제하는 메서드
     * @param reviewId
     * @return 200
     */
    @DeleteMapping(value = "/reviews/{reviewId}")
    public BaseResponse<ReviewResponseDto> deleteReview(
                                @PathVariable("reviewId") UUID reviewId,
                                @AuthenticationPrincipal UserDetails user){
        UUID userId = getUserId(user);
        reviewService.deleteReview(reviewId, userId);
        return BaseResponse.success();
    }
}
