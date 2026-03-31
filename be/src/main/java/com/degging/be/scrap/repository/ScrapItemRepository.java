package com.degging.be.scrap.repository;

import com.degging.be.cafe.entity.CafeEntity;
import com.degging.be.scrap.entity.ScrapEntity;
import com.degging.be.scrap.entity.ScrapItemEntity;
import org.springframework.data.domain.Pageable;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Modifying;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;
import org.springframework.stereotype.Repository;
import org.springframework.transaction.annotation.Transactional;

import java.util.List;
import java.util.Optional;
import java.util.UUID;

/**
 * 스크랩-카페 연관관계 레포지토리
 */
@Repository
public interface ScrapItemRepository extends JpaRepository<ScrapItemEntity, UUID> {
    // 회원의 특정 스크랩 중 최신 썸네일 4장 가져오기
    @Query("SELECT c.thumbnailUrl FROM ScrapItemEntity si " +
            "JOIN si.cafe c " +
            "WHERE si.scrap.scrapId = :scrapId " +
            "ORDER BY si.createdAt DESC")
    List<String> findTopImageUrlsByScrapId(@Param("scrapId") UUID scrapId, Pageable pageable);

    // 특정 유저의 전체 스크랩 중 최신 썸네일 4장 가져오기
    @Query("SELECT c.thumbnailUrl FROM ScrapItemEntity si " +
            "JOIN si.cafe c " +
            "WHERE si.scrap.user.userId = :userId " +
            "ORDER BY si.createdAt DESC")
    List<String> findTopImageUrlsByUserId(@Param("userId") UUID userId, Pageable pageable);

    // 특정 스크랩 폴더에서 특정 카페 삭제하기
    @Modifying(flushAutomatically = true, clearAutomatically = true)
    void deleteByScrap_ScrapIdAndCafe_CafeId(UUID scrapId, UUID cafeId);

    // 중복 확인
    boolean existsByScrapAndCafe(ScrapEntity scrap, CafeEntity cafe);

    // 특정 유저의 스크랩 전체 조회
    Optional<List<ScrapItemEntity>> findAllByScrapUserUserId(UUID userId);

    // 기본 스크랩에서 특정 카페를 삭제
    // 전에 조회한 Entity 에도 변경사항이 반영되어 삭제됨
    @Modifying(flushAutomatically = true, clearAutomatically = true)
    @Query("DELETE FROM ScrapItemEntity si " +
            "WHERE si.cafe.cafeId = :cafeId " +
            "AND si.scrap.user.userId = :userId " +
            "AND si.scrap.isDefault = true")
    void deleteDefaultScrapItem(@Param("userId") UUID userId, @Param("cafeId") UUID cafeId);

    // 기본 스크랩에 해당 카페가 있는지 확인
    boolean existsByScrap_User_UserIdAndScrap_IsDefaultTrueAndCafe_CafeId(UUID userId, UUID cafeId);
}
