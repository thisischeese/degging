package com.degging.be.cafe.repository;

import com.degging.be.cafe.entity.CafeEntity;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;

import java.util.List;
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
}