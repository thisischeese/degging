package com.degging.be.cafe.repository;

import com.degging.be.cafe.entity.CafeEntity;
import com.degging.be.cafe.entity.CafeStatus;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;
import org.springframework.data.domain.Slice;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;

import java.util.List;
import java.util.Optional;
import java.util.UUID;

public interface CafeRepository extends JpaRepository<CafeEntity, UUID> {

    /**
     * 상가업소번호(bizesId) 중복 여부 확인
     */
    boolean existsByBizesId(String bizesId);

    /**
     * 카카오 장소 식별자 중복 여부
     */
    boolean existsByKakaoPlaceId(String kakaoPlaceId);

    /**
     * 여러 카카오 플레이스 ID 중 이미 DB에 존재하는 ID 리스트 조회
     */
    @Query("SELECT c.kakaoPlaceId FROM CafeEntity c WHERE c.kakaoPlaceId IN :kakaoPlaceIds")
    List<String> findAllExistingKakaoPlaceIds(@Param("kakaoPlaceIds") List<String> kakaoPlaceIds);

    /**
     * 이름을 기반으로 카페 목록 조회
     */
    List<CafeEntity> findAllByName(String name);

    /**
     * 정제된 브랜드명(brandName)이 10개 이상인 목록 조회
     */
    @Query("SELECT c.brandName " +
            "FROM CafeEntity c " +
            "GROUP BY c.brandName " +
            "HAVING COUNT(c.brandName) >= 10")
    List<String> findBrandNamesExceedingThreshold();

    /**
     * 특정 브랜드명을 가진 모든 카페 목록 조회
     */
    List<CafeEntity> findAllByBrandName(String brandName);

//----------------------------------------------------------------------------------------------

    /**
     * 카페 상세 조회를 위한 페치 조인 쿼리
     */
    @Query("SELECT DISTINCT c FROM CafeEntity c " +
            "LEFT JOIN FETCH c.ratingStats " +
            "LEFT JOIN FETCH c.vibeTags vt " +
            "LEFT JOIN FETCH vt.vibe " +
            "WHERE c.cafeId = :cafeId")
    Optional<CafeEntity> findByIdWithDetail(@Param("cafeId") UUID cafeId);

    /**
     * 사용자 현재 위치 기준 반경 내 카페 목록 조회
     *
     * @param point            사용자의 현재 위치
     * @param radius           조회 반경
     * @param includeFranchise 프랜차이즈 포함 여부
     * @return 반경 내 카페 엔티티 리스트
     */
    @Query("SELECT c FROM CafeEntity c " +
            "WHERE ST_Distance_Sphere(c.location, ST_GeomFromText(:point, 4326)) <= :radius " +
            "AND (:includeFranchise = true OR c.franchise = false)")
    List<CafeEntity> findMarkersByRadius(
            @Param("point") String point,
            @Param("radius") Double radius,
            @Param("includeFranchise") boolean includeFranchise);

//----------------------------------------------------------------------------------------------

    /**
     * 썸네일 이미지가 존재하고 특정 영업 상태인 카페를 상위 100개 조회
     * @param status 조회할 카페의 영업 상태 (ex. OPEN)
     * @return 필터링된 카페 엔티티 리스트
     */
    List<CafeEntity> findTop100ByThumbnailUrlIsNotNullAndStatus(CafeStatus status);

    /**
     * 온보딩 분석을 위해 필요한 분위기 태그 정보만 선별적으로 조회합니다.
     *
     * @param cafeIds 카페 식별자 목록
     * @return 분위기 태그가 포함된 카페 엔티티 목록
     */
    @Query("SELECT DISTINCT c FROM CafeEntity c " +
            "JOIN FETCH c.vibeTags vt " +
            "JOIN FETCH vt.vibe " +
            "WHERE c.cafeId IN :cafeIds")
    List<CafeEntity> findAllWithVibesById(@Param("cafeIds") List<UUID> cafeIds);

//----------------------------------------------------------------------------------------------

    /**
     * [바텀시트] 반경 내 카페 조회 - 거리순
     *
     * @param point            사용자 현재 위치
     * @param radius           조회 반경
     * @param includeFranchise 프랜차이즈 포함 여부
     * @param pageable         페이징 정보
     * @return 거리순 정렬된 카페 Slice
     */
    @Query("SELECT c FROM CafeEntity c " +
            "WHERE ST_Distance_Sphere(c.location, ST_GeomFromText(:point, 4326)) <= :radius " +
            "AND (:includeFranchise = true OR c.franchise = false) " +
            "ORDER BY ST_Distance_Sphere(c.location, ST_GeomFromText(:point, 4326)) ASC")
    Slice<CafeEntity> findBottomSheetByDistance(
            @Param("point") String point,
            @Param("radius") Double radius,
            @Param("includeFranchise") boolean includeFranchise,
            Pageable pageable);

    /**
     * [바텀시트] 반경 내 카페 조회 - 별점 높은 순
     *
     * ratingSum / reviewCount 기준으로 내림차순 정렬
     */
    @Query("SELECT c FROM CafeEntity c " +
            "LEFT JOIN c.ratingStats rs " +
            "WHERE ST_Distance_Sphere(c.location, ST_GeomFromText(:point, 4326)) <= :radius " +
            "AND (:includeFranchise = true OR c.franchise = false) " +
            "ORDER BY CASE WHEN rs.reviewCount > 0 THEN CAST(rs.ratingSum AS double) / rs.reviewCount ELSE 0 END DESC")
    Slice<CafeEntity> findBottomSheetByRating(
            @Param("point") String point,
            @Param("radius") Double radius,
            @Param("includeFranchise") boolean includeFranchise,
            Pageable pageable);

    /**
     * [바텀시트] 반경 내 카페 조회 - 리뷰 많은 순
     *
     * reviewCount 기준으로 내림차순 정렬
     */
    @Query("SELECT c FROM CafeEntity c " +
            "LEFT JOIN c.ratingStats rs " +
            "WHERE ST_Distance_Sphere(c.location, ST_GeomFromText(:point, 4326)) <= :radius " +
            "AND (:includeFranchise = true OR c.franchise = false) " +
            "ORDER BY COALESCE(rs.reviewCount, 0) DESC")
    Slice<CafeEntity> findBottomSheetByReviewCount(
            @Param("point") String point,
            @Param("radius") Double radius,
            @Param("includeFranchise") boolean includeFranchise,
            Pageable pageable);

    /**
     * [바텀시트] 반경 내 카페 조회 - 추천순
     * TODO: AI 연동을 통한 추천 카페 리스트업 예정
     */
    
    /**
     * AI 크롤링이 필요한 카페 목록 조회 (썸네일이 없는 카페 기준)
     *
     * @param pageable 페이징 정보
     * @return 썸네일이 없는 카페 Page
     */
    Page<CafeEntity> findAllByThumbnailUrlIsNull(Pageable pageable);
    
}
