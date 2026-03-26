package com.degging.be.review.repository;

import com.degging.be.review.dto.response.ReviewResponse;
import com.degging.be.review.entity.ReviewEntity;
import org.springframework.data.domain.Pageable;
import org.springframework.data.domain.Slice;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;
import org.springframework.stereotype.Repository;

import java.util.Optional;
import java.util.UUID;

/**
 * 카페 리뷰 데이터 접근을 위한 레포지토리
 */
@Repository
public interface ReviewRepository extends JpaRepository<ReviewEntity, UUID> {
    // 리뷰 작성자, 카페, 내용을 이용한 중복 체크
    boolean existsByUserUserIdAndCafeCafeIdAndContent(UUID userId, UUID cafeId, String content);

    // 카페 ID로 전체 리뷰 조회 (리뷰, 리뷰 이미지, 회원 정보), 최신순으로 가져옴
    @Query("SELECT r FROM ReviewEntity r " +
            "JOIN FETCH r.user " +  // User는 List가 아니니까 안전!
            "WHERE r.cafe.cafeId = :cafeId " +
            "ORDER BY r.createdAt DESC")
    Slice<ReviewEntity> findAllByCafeIdWithImages(@Param("cafeId") UUID cafeId, Pageable pageable);

    // 카페 ID로 전체 리뷰 조회 (리뷰, 리뷰 이미지, 회원 정보) 필요한 정보만 DTO 에 담아, 최신순으로 가져옴
    @Query("SELECT new com.degging.be.review.dto.response.ReviewResponse(" +
            "r.reviewId, r.rating, r.content, r.createdAt, r.updatedAt, u.profile.nickname) " +
            "FROM ReviewEntity r " +
            "JOIN r.user u " + // 닉네임은 필요하니까 유저만 조인
            "WHERE r.cafe.cafeId = :cafeId " + // 카페 객체가 아닌 ID값만 조건으로 사용
            "ORDER BY r.createdAt DESC")
    Slice<ReviewResponse> findReviewResponseByCafeId(@Param("cafeId") UUID cafeId, Pageable pageable);

    // 특정 리뷰 상세 정보 조회 (리뷰, 리뷰 이미지, 회원 정보, 카페 정보)
    @Query("SELECT r FROM ReviewEntity r " +
            "JOIN FETCH r.user " +
            "JOIN FETCH r.cafe " +
            "LEFT JOIN FETCH r.reviewImages " +
            "WHERE r.reviewId = :reviewId")
    Optional<ReviewEntity> findDetailById(@Param("reviewId") UUID reviewId);

    // 사용자 ID로 전체 리뷰 조회 (리뷰, 리뷰 이미지), 최신순으로 가져옴
    @Query("SELECT DISTINCT r FROM ReviewEntity r " +
            "LEFT JOIN FETCH r.reviewImages " +
            "WHERE r.user.userId = :userId " +
            "ORDER BY r.createdAt DESC")
    Slice<ReviewEntity> findAllByUserIdWithImages(UUID userId, Pageable pageable);
}
