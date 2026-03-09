package com.degging.be.review.service;

import com.degging.be.global.exception.BaseException;
import com.degging.be.global.exception.errorcode.CafeErrorCode;
import com.degging.be.global.exception.errorcode.CommonErrorCode;
import com.degging.be.global.exception.errorcode.ErrorCode;
import com.degging.be.review.dto.request.ReviewRequestDto;
import com.degging.be.review.dto.request.ReviewUpdateRequestDto;
import com.degging.be.review.entity.ReviewEntity;
import com.degging.be.review.entity.ReviewImageEntity;
import com.degging.be.review.repository.ReviewImageRepository;
import com.degging.be.review.repository.ReviewRepository;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.web.multipart.MultipartFile;

import java.util.ArrayList;
import java.util.List;
import java.util.UUID;

/**
 * 사용자 리뷰를 관리하는 클래스
 */
@Service
@Slf4j
@RequiredArgsConstructor
public class ReviewService {
    private final ReviewRepository reviewRepository;
    private final ReviewImageRepository reviewImageRepository;
//    private final CafeRepository cafeRepository;

    // 리뷰 생성 메서드
    @Transactional
    public void createReview(ReviewRequestDto request, UUID loginUser, List<MultipartFile> images, UUID cafeId){
        // 유효성 검증
        validateUser(loginUser);
        checkCafeValidation(cafeId);

        // Dto -> Entity 후 Review 테이블에 저장
        ReviewEntity entity = reviewRepository.save(request.toEntity(loginUser, cafeId));

        // Review_Image 테이블에 저장
        uploadReviewImages(entity, images, 0);
    }

    // 리뷰 수정 메서드
    @Transactional
    public void updateReview(ReviewUpdateRequestDto request, UUID loginUser, List<MultipartFile> images, UUID reviewId){
        log.info("삭제할 이미지 IDs: {}", request.getDeleteImageIds());
        validateUser(loginUser);

        ReviewEntity review = reviewRepository.findById(reviewId)
                .orElseThrow(()-> new BaseException(CafeErrorCode.REVIEW_NOT_FOUND));
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

    // 리뷰 생성/수정의 이미지 업로드 로직
    public void uploadReviewImages(ReviewEntity review, List<MultipartFile> images, int startOrder){
        if (images == null || images.isEmpty()) return;
        // 빈 값으로 보냈을 때 -> 내용물이 없는 경우
        if (images.getFirst().isEmpty()) return;

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

    // 리뷰 삭제하는 메서드
    @Transactional
    public void deleteReview(UUID reviewId, UUID loginUser){
        // 유효성
        validateUser(loginUser);
        ReviewEntity review = reviewRepository.findById(reviewId)
                .orElseThrow(()-> new BaseException(CafeErrorCode.REVIEW_NOT_FOUND));
        validateAuthor(review, loginUser);

        // 리뷰 삭제 (사진은 cascade 로 삭제)
        reviewRepository.deleteById(reviewId);
    }

    /**
     * 유효성 검증 코드
     */

    // user 정보 체크
    private void validateUser(UUID loginUser) {
        // 값이 제대로 들어오지 않음, jwt 를 쓰지만 한번 더 체크
        if (loginUser == null) {
            throw new BaseException(CommonErrorCode.UNAUTHORIZED);
        }
    }

    // 작성자 본인 체크
    public void validateAuthor(ReviewEntity review, UUID loginUser) {
        if (!review.getUserId().equals(loginUser)) {
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
}
