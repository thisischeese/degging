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
        checkValidation(request, loginUser);

        // Dto -> Entity 후 Review 테이블에 저장
        ReviewEntity entity = reviewRepository.save(request.toEntity(loginUser, cafeId));

        if (images != null && !images.isEmpty()){
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
                        .review(entity)
                        .imageUrl(tempUrl)
                        .sortOrder(i)
                        .build();
                entities.add(imageEntity);
            }
            reviewImageRepository.saveAll(entities);
        }
    }

    /**
     * 유효성 검증 코드
     */

    public void checkValidation(ReviewRequestDto request, UUID loginUser) {
        // 값이 제대로 들어오지 않음, jwt 를 쓰지만 한번 더 체크
        if (loginUser == null) {
            throw new BaseException(CommonErrorCode.UNAUTHORIZED);
        }
        // 카페 존재 여부 확인, cafe 연결 후 주석 지우기
//        cafeRepository.ExistedById(request.getCafeId()).orElseThrow(
//                new BaseException(CafeErrorCode.CAFE_NOT_FOUND));
    }
}
