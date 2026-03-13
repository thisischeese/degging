package com.degging.be.scrap.repository;

import com.degging.be.scrap.entity.ScrapEntity;
import com.degging.be.user.entity.User;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;

import java.util.List;
import java.util.Optional;
import java.util.UUID;

/**
 * 카페 스크랩 데이터 접근을 위한 레포지토리
 */
public interface ScrapRepository extends JpaRepository<ScrapEntity, UUID> {
    // 특정 사용자의 스크랩명 중복 확인
    boolean existsByNameAndUser(String name, User user);

    // 특정 사용자의 스크랩 리스트 조회
    List<ScrapEntity> findAllByUserUserId(UUID user_userId);

    // 스크랩 상세 조회 (카페 정보 포함)
    @Query("SELECT s FROM ScrapEntity s " +
            "LEFT JOIN FETCH s.scrapItems si " + // ScrapItem과 조인
            "LEFT JOIN FETCH si.cafe c " +       // Cafe까지 조인 (여기서 thumbnailUrl은 이미 포함됨)
            "WHERE s.scrapId = :scrapId")
    Optional<ScrapEntity> findByIdWithCafesAndImages(@Param("scrapId") UUID scrapId);
}
