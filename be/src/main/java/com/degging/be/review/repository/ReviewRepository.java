package com.degging.be.review.repository;

import com.degging.be.review.entity.ReviewEntity;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;
import org.springframework.stereotype.Repository;

import java.util.List;
import java.util.Optional;
import java.util.UUID;

/**
 * 카페 리뷰 데이터 접근을 위한 레포지토리
 */
@Repository
public interface ReviewRepository extends JpaRepository<ReviewEntity, UUID> {
    // 리뷰 작성자, 카페, 내용을 이용한 중복 체크
    boolean existsByUserIdAndCafeIdAndContent(UUID loginUser, UUID cafeId, String content);

    // 카페 ID로 전체 리뷰 조회 (리뷰, 리뷰 이미지, 회원 정보), 최신순으로 가져옴
    @Query("SELECT DISTINCT r FROM ReviewEntity r " +
            "LEFT JOIN FETCH r.reviewImages " +
            "LEFT JOIN FETCH r.user " +
            "WHERE r.cafeId = :cafeId " +
            "ORDER BY r.createdAt DESC") 
    List<ReviewEntity> findAllByCafeIdWithImages(UUID cafeId);

    // 특정 리뷰 상세 정보 조회 (리뷰, 리뷰 이미지, 회원 정보, 카페 정보)
    @Query("SELECT r FROM ReviewEntity r " +
            "JOIN FETCH r.user " +
            "JOIN FETCH r.cafeId " +       // 카페 조인 (아직 cafe 도메인이 없어서 id 로 대체)
            "LEFT JOIN FETCH r.reviewImages " +
            "WHERE r.reviewId = :reviewId")
    Optional<ReviewEntity> findDetailById(@Param("reviewId") UUID reviewId);
}
