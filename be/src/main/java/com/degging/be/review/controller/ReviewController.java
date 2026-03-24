package com.degging.be.review.controller;

import com.degging.be.global.dto.BaseResponse;
import com.degging.be.global.exception.BaseException;
import com.degging.be.global.exception.errorcode.CommonErrorCode;
import com.degging.be.review.dto.request.ReviewRequest;
import com.degging.be.review.dto.request.ReviewUpdateRequest;
import com.degging.be.review.dto.response.CommonSliceResponse;
import com.degging.be.review.dto.response.MyReviewResponse;
import com.degging.be.review.dto.response.ReviewDetailResponse;
import com.degging.be.review.dto.response.ReviewResponse;
import com.degging.be.review.service.ReviewService;
import jakarta.validation.Valid;
import lombok.RequiredArgsConstructor;
import org.springframework.data.domain.Pageable;
import org.springframework.data.domain.Slice;
import org.springframework.data.domain.Sort;
import org.springframework.data.web.PageableDefault;
import org.springframework.http.MediaType;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.multipart.MultipartFile;
import org.springframework.security.core.annotation.AuthenticationPrincipal;
import org.springframework.security.core.userdetails.UserDetails;

import java.io.IOException;
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
                    @AuthenticationPrincipal UserDetails user) throws IOException {
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
     * @param pageable 페이징 설정 (기본값: 10개씩 조회, 생성일자 기준 내림차순 정렬)
     * @return 200, ReviewResponse 리스트 (리뷰, 이미지, 작성자 정보)
     */
    @GetMapping("/cafes/{cafeId}/reviews")
    public BaseResponse<CommonSliceResponse<ReviewResponse>> getReviews(
                    @AuthenticationPrincipal UserDetails user,
                    @PathVariable("cafeId") UUID cafeId,
                    @PageableDefault(size = 10, sort = "createdAt", direction = Sort.Direction.DESC) Pageable pageable){
        UUID userId = getUserId(user);
        Slice<ReviewResponse> reviews = reviewService.getReviewsByCafeId(cafeId, userId, pageable);
        return BaseResponse.success(CommonSliceResponse.from(reviews));
    }

    /**
     * 특정 리뷰의 상세정보를 조회하는 메서드
     * @param user JWT 에서 꺼낸 로그인 정보 (인증된 사용자)
     * @param reviewId 조회할 리뷰 ID
     * @return 200, ReviewDetailResponse (리뷰, 이미지, 작성자 정보, 카페 정보(상호명, 큐레이션 1줄, 위치))
     */
    @GetMapping("/reviews/{reviewId}")
    public BaseResponse<ReviewDetailResponse> getReviewDetail(
                    @AuthenticationPrincipal UserDetails user,
                    @PathVariable("reviewId") UUID reviewId){
        UUID userId = getUserId(user);
        ReviewDetailResponse detail = reviewService.getReviewDetail(reviewId, userId);
        return BaseResponse.success(detail);
    }

    /**
     * 로그인한 유저의 전체 리뷰를 조회하는 메서드
     * @param user JWT 에서 꺼낸 로그인 정보 (인증된 사용자)
     * @param pageable 페이징 설정 (기본값: 10개씩 조회, 생성일자 기준 내림차순 정렬)
     * @return 200, 다음 페이지 여부(hasNext)가 포함된 리뷰 목록 Slice
     */
    @GetMapping("/reviews/mine")
    public BaseResponse<CommonSliceResponse<MyReviewResponse>> getMyReviews(
            @AuthenticationPrincipal UserDetails user,
            @PageableDefault(size = 10, sort = "createdAt", direction = Sort.Direction.DESC) Pageable pageable){
        UUID userId = getUserId(user);
        CommonSliceResponse<MyReviewResponse> reviews = reviewService.getReviewsByUserId(userId, pageable);
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
                    @AuthenticationPrincipal UserDetails user) throws IOException {
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
