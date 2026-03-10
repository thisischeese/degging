package com.degging.be.review.repository;

import com.degging.be.review.entity.ReviewEntity;
import com.degging.be.review.entity.ReviewImageEntity;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

import java.util.List;
import java.util.UUID;

/**
 * 카페 리뷰 이미지 데이터 접근을 위한 레포지토리
 */
@Repository
public interface ReviewImageRepository extends JpaRepository<ReviewImageEntity, UUID> {
    // sort order 에 따라 오름차로 리뷰를 가져옴
    List<ReviewImageEntity> findByReviewOrderBySortOrderAsc(ReviewEntity review);

    // Review 의 이미지 개수 조회
    int countByReview(ReviewEntity review);
}
