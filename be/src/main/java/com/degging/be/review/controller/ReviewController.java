package com.degging.be.review.controller;

import com.degging.be.global.dto.BaseResponse;
import com.degging.be.global.exception.BaseException;
import com.degging.be.global.exception.errorcode.CommonErrorCode;
import com.degging.be.review.dto.request.ReviewRequest;
import com.degging.be.review.dto.request.ReviewUpdateRequest;
import com.degging.be.review.dto.response.ReviewResponse;
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

/**
 * 카페 리뷰 생성, 수정, 삭제 등 리뷰 관련 API 컨트롤러
 */
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
     * @param cafeId 카페 ID
     * @param request 리뷰 내용을 담은 Request 객체
     * @param user JWT 에서 꺼낸 로그인 정보 (인증된 사용자)
     * @return 200
     */
    @PostMapping(value = "/cafes/{cafeId}/reviews", consumes = {MediaType.MULTIPART_FORM_DATA_VALUE})
    public BaseResponse<ReviewResponse> createReview(
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
     * 특정 카페의 전체 리뷰를 조회하는 메서드
     * @param user JWT 에서 꺼낸 로그인 정보 (인증된 사용자)
     * @param cafeId 리뷰를 조회할 카페 ID
     * @return 200, ReviewResponse 리스트 (리뷰, 이미지, 작성자 정보)
     */
    @GetMapping("/cafes/{cafeId}/reviews")
    public BaseResponse<List<ReviewResponse>> getReviews(
                    @AuthenticationPrincipal UserDetails user,
                    @PathVariable("cafeId") UUID cafeId){
        UUID userId = getUserId(user);
        List<ReviewResponse> reviews = reviewService.getReviewsByCafeId(cafeId, userId);
        return BaseResponse.success(reviews);
    }


    /**
     * 특정 ID 리뷰를 수정하는 메서드
     * @param reviewId 수정할 카페 리뷰 ID
     * @param request 평점, 내용, 삭제할 사진 ID 리스트, 새로 추가한 사진 리스트
     * @param user JWT 에서 꺼낸 로그인 정보 (인증된 사용자)
     * @return 200
     */
    @PatchMapping(value = "/reviews/{reviewId}", consumes = {MediaType.MULTIPART_FORM_DATA_VALUE})
    public BaseResponse<ReviewResponse> updateReview(
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
     * @param reviewId 삭제할 리뷰 ID
     * @param user JWT 에서 꺼낸 로그인 정보 (인증된 사용자)
     * @return 200
     */
    @DeleteMapping(value = "/reviews/{reviewId}")
    public BaseResponse<ReviewResponse> deleteReview(
                                @PathVariable("reviewId") UUID reviewId,
                                @AuthenticationPrincipal UserDetails user){
        UUID userId = getUserId(user);
        reviewService.deleteReview(reviewId, userId);
        return BaseResponse.success();
    }
}
