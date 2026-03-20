package com.degging.be.scrap.repository;

import com.degging.be.scrap.entity.ScrapEntity;
import com.degging.be.user.entity.UserEntity;
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

    // 스크랩 조회 시 필요한 항목만 꺼내기 위한 Projection
    public interface ScrapSummaryProjection {
        UUID getScrapId();
        String getName();
        String getColor();
        List<String> getThumbnailUrls();
    }

    // 특정 사용자의 스크랩명 중복 확인
    boolean existsByNameAndUser(String name, UserEntity user);

    // 특정 사용자의 스크랩 리스트 조회
    List<ScrapEntity> findAllByUserUserId(UUID user_userId);

    // 스크랩 상세 조회 (카페 정보 포함)
    @Query("SELECT s FROM ScrapEntity s " +
            "LEFT JOIN FETCH s.scrapItems si " + // ScrapItem과 조인
            "LEFT JOIN FETCH si.cafe c " +       // Cafe까지 조인 (여기서 thumbnailUrl은 이미 포함됨)
            "WHERE s.scrapId = :scrapId")
    Optional<ScrapEntity> findByIdWithCafesAndImages(@Param("scrapId") UUID scrapId);

    /**
     * 특정 사용자의 특정 카페 스크랩 여부 확인
     *
     * @param userId 조회할 사용자 ID
     * @param cafeId 카페 ID
     * @return 스크랩 여부
     */
    @Query("SELECT COUNT(si) > 0 FROM ScrapItemEntity si " +
            "WHERE si.scrap.user.userId = :userId " +
            "AND si.cafe.cafeId = :cafeId")
    boolean existsByUserIdAndCafeId(@Param("userId") UUID userId, @Param("cafeId") UUID cafeId);

    /**
     * 특정 사용자가 특정 카페를 스크랩한 폴더의 색상을 조회
     *
     * @param userId 조회할 사용자 ID
     * @param cafeId 카페 ID
     * @return 스크랩 폴더의 색상
     */
    @Query("SELECT s.color FROM ScrapItemEntity si " +
            "JOIN si.scrap s " +
            "WHERE s.user.userId = :userId " +
            "AND si.cafe.cafeId = :cafeId")
    String findScrapColorByUserIdAndCafeId(@Param("userId") UUID userId, @Param("cafeId") UUID cafeId);


    @Query("SELECT s.scrapId as scrapId, s.name as name, s.color as color, s.thumbnailUrls as thumbnailUrls " +
            "FROM ScrapEntity s WHERE s.user.userId = :userId")
    List<ScrapSummaryProjection> findScrapSummariesByUserId(@Param("userId") UUID userId);
}
