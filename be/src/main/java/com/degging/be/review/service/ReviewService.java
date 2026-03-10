package com.degging.be.review.service;

import com.degging.be.global.exception.BaseException;
import com.degging.be.global.exception.errorcode.CafeErrorCode;
import com.degging.be.global.exception.errorcode.CommonErrorCode;
import com.degging.be.global.exception.errorcode.UserErrorCode;
import com.degging.be.review.dto.request.ReviewRequest;
import com.degging.be.review.dto.request.ReviewUpdateRequest;
import com.degging.be.review.dto.response.ReviewDetailResponse;
import com.degging.be.review.dto.response.ReviewResponse;
import com.degging.be.review.entity.ReviewEntity;
import com.degging.be.review.entity.ReviewImageEntity;
import com.degging.be.review.repository.ReviewImageRepository;
import com.degging.be.review.repository.ReviewRepository;
import com.degging.be.user.entity.User;
import com.degging.be.user.repository.UserRepository;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.web.multipart.MultipartFile;

import java.util.ArrayList;
import java.util.List;
import java.util.UUID;

/**
 * 카페 리뷰를 관리하는 클래스
 */
@Service
@Slf4j
@RequiredArgsConstructor
public class ReviewService {
    private final ReviewRepository reviewRepository;
    private final ReviewImageRepository reviewImageRepository;
    private final UserRepository userRepository;
//    private final CafeRepository cafeRepository;

    /**
     * 리뷰 생성 메서드
     */
    @Transactional
    public void createReview(ReviewRequest request, UUID loginUser, List<MultipartFile> images, UUID cafeId){
        // 유효성 검증 및 객체 조회
        User user = getValidUser(loginUser);
        checkCafeValidation(cafeId);

        // 중복 체크
        boolean isDuplicate = reviewRepository.existsByUserIdAndCafeIdAndContent(
                loginUser, cafeId, request.getContent()
        );

        if (isDuplicate) {
            throw new BaseException(CafeErrorCode.REVIEW_ALREADY_EXISTS);
        }

        // Dto -> Entity 후 Review 테이블에 저장
        ReviewEntity entity = reviewRepository.save(request.toEntity(user, cafeId));

        // Review_Image 테이블에 저장
        uploadReviewImages(entity, images, 0);
    }

    /**
     * 특정 카페 전체 리뷰 조회 메서드
     */
    @Transactional
    public List<ReviewResponse> getReviewsByCafeId(UUID cafeId, UUID userId) {
        // 유효성 검증
        validateUser(userId);
        checkCafeValidation(cafeId);
        
        // 카페 ID로 리뷰와 리뷰, 이미지, 작성자 조회하여 반환
        List<ReviewEntity> reviews = reviewRepository.findAllByCafeIdWithImages(cafeId);
        return reviews.stream()
                .map(ReviewResponse::toDto)
                .toList();
    }

    /**
     * 특정 리뷰 상세 조회 메서드
     */
    @Transactional(readOnly = true)
    public ReviewDetailResponse getReviewDetail(UUID reviewId, UUID userId) {
        // 유효성 검증
        validateUser(userId);
        ReviewEntity review = getValidReview(reviewId);

        // Entity -> DTO
        return ReviewDetailResponse.toDto(review);
    }

    /**
     * 리뷰 수정 메서드
     */
    @Transactional
    public void updateReview(ReviewUpdateRequest request, UUID loginUser, List<MultipartFile> images, UUID reviewId){
        log.info("삭제할 이미지 IDs: {}", request.getDeleteImageIds());
        // 유효성 검증
        validateUser(loginUser);
        ReviewEntity review = getValidReview(reviewId);
        // 본인 확인
        validateAuthor(review, loginUser);
        
        // 기존 이미지가 존재한다면 삭제 후 진행
        if (request.getDeleteImageIds() != null && !request.getDeleteImageIds().isEmpty()){
            reviewImageRepository.deleteAllById(request.getDeleteImageIds());
            reviewImageRepository.flush(); // 즉시 DB와 동기화
        }

        // 삭제 후 기존 이미지 순서 재설정
        List<ReviewImageEntity> entities = reviewImageRepository.findByReviewOrderBySortOrderAsc(review);
        int order = 0;
        for (ReviewImageEntity e : entities){
            e.updateSortOrder(order++);
        }
        // 새로 반영된 내용 추가 저장
        uploadReviewImages(review, images, order);

        // 변경된 내용, 별점 반영하여 저장, Dirty Checking 이용
        review.update(request);
    }

    /**
     * 리뷰 생성/수정의 이미지 업로드 메서드
     */
    public void uploadReviewImages(ReviewEntity review, List<MultipartFile> images, int startOrder){
        if (images == null || images.isEmpty() || images.getFirst().isEmpty()) return;

        // 이미지 개수 3개로 제한
        int currentImgCount = reviewImageRepository.countByReview(review);
        if (currentImgCount + images.size() > 3){
            throw new BaseException(CafeErrorCode.IMAGE_COUNT_EXCEEDED);
        }
        // 리뷰 Entity 를 담을 리스트
        List<ReviewImageEntity> entities = new ArrayList<>();

        // 이미지를 꺼내 S3 업로드 후 URL 반환 받아 DB에 저장
        for (int i = 0; i < images.size(); i++){
            MultipartFile file = images.get(i);

            // TODO : S3 업로드 후 url 반환
            // 임시 이미지 url
            String tempUrl = "https://s3.cloud/test/" + file.getOriginalFilename();

            // 이미지 Entity 생성 후 저장
            ReviewImageEntity imageEntity = ReviewImageEntity.builder()
                    .review(review)
                    .imageUrl(tempUrl)
                    .sortOrder(startOrder + i)
                    .build();
            entities.add(imageEntity);
        }
        // Batch 로 한번에 저장
        reviewImageRepository.saveAll(entities);
    }

    /**
     * 리뷰 삭제하는 메서드
     */
    @Transactional
    public void deleteReview(UUID reviewId, UUID loginUser){
        // 유효성
        validateUser(loginUser);
        ReviewEntity review = reviewRepository.findById(reviewId)
                .orElseThrow(()-> new BaseException(CafeErrorCode.REVIEW_NOT_FOUND));
        validateAuthor(review, loginUser);

        // 리뷰 삭제 (사진은 cascade 로 삭제)
        reviewRepository.delete(review);
    }

    /**
     * 유효성 검증 코드
     */
    // user 정보 체크 3가지
    // 1. 존재 여부만 체크
    private void validateUser(UUID userId) {
        getValidUser(userId); // 내부에서 호출만 하고 끝
    }

    // 2. 존재 여부 체크 및 User 반환
    private User getValidUser(UUID loginUser){
        return userRepository.findById(loginUser)
                .orElseThrow(()-> new BaseException(UserErrorCode.USER_NOT_FOUND));
    }

    // 3. 작성자 본인 체크
    public void validateAuthor(ReviewEntity review, UUID loginUser) {
        if (!review.getUser().getUserId().equals(loginUser)) {
            throw new BaseException(CommonErrorCode.FORBIDDEN);
        }
    }

    // 카페 존재 체크
    public void checkCafeValidation(UUID cafeId){
        if (cafeId == null) return;
        // 카페 존재 여부 확인, cafe 연결 후 주석 지우기
//        return cafeRepository.ExistedById(request.getCafeId()).orElseThrow(
//                  new BaseException(CafeErrorCode.CAFE_NOT_FOUND));
    }

    // 리뷰 존재 체크
    public ReviewEntity getValidReview(UUID reviewId){
        return reviewRepository.findById(reviewId)
                .orElseThrow(()-> new BaseException(CafeErrorCode.REVIEW_NOT_FOUND));
    }
}
