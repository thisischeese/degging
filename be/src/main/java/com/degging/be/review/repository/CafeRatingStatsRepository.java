package com.degging.be.review.repository;

import com.degging.be.cafe.entity.CafeRatingStatsEntity;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

import java.util.UUID;

/**
 * 카페 평점을 관리하는 레포지토리
 */
@Repository
public interface CafeRatingStatsRepository extends JpaRepository<CafeRatingStatsEntity, UUID> {
}
