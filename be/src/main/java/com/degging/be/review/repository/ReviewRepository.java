package com.degging.be.review.repository;

import com.degging.be.review.entity.ReviewEntity;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

import java.util.UUID;

@Repository
public interface ReviewRepository extends JpaRepository<ReviewEntity, UUID> {
    // 리뷰 작성자, 카페, 내용을 이용한 중복 체크
    boolean existsByUserIdAndCafeIdAndContent(UUID loginUser, UUID cafeId, String content);
}
