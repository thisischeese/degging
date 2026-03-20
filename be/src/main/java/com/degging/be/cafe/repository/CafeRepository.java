package com.degging.be.cafe.repository;

import com.degging.be.cafe.dto.response.internal.CafeMapResponse;
import com.degging.be.cafe.entity.CafeEntity;
import com.degging.be.cafe.entity.CafeStatus;
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
     * 카카오 상세 정보가 비어있는 카페 목록 조회
     *
     * 전화번호, 카카오 맵 URL 설정되지 않은 엔티티를 찾아 반환
     */
    List<CafeEntity> findAllByPhoneIsNullAndKakaoMapUrlIsNull();

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
}