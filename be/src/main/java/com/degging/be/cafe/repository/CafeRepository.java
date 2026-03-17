package com.degging.be.cafe.repository;

import com.degging.be.cafe.dto.response.internal.CafeMapResponse;
import com.degging.be.cafe.entity.CafeEntity;
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
    @Query("SELECT c FROM CafeEntity c " +
            "LEFT JOIN FETCH c.ratingStats " +
            "LEFT JOIN FETCH c.images " +
            "LEFT JOIN FETCH c.menus " +
            "LEFT JOIN FETCH c.vibeTags vt " +
            "LEFT JOIN FETCH vt.vibe " +
            "WHERE c.cafeId = :cafeId")
    Optional<CafeEntity> findByIdWithDetail(@Param("cafeId") UUID cafeId);

    /**
     * 사용자 현재 위치 기준 반경 내 카페 목록 조회
     *
     * @param point 사용자의 현재 위치
     * @param radius 조회 반경
     * @return 반경 내 카페 엔티티 리스트
     */
    @Query("SELECT c FROM CafeEntity c " +
            "WHERE ST_Distance_Sphere(c.location, ST_GeomFromText(:point, 4326)) <= :radius")
    List<CafeEntity> findMarkersByRadius(@Param("point") String point, @Param("radius") Double radius);
}