package com.degging.be.cafe.repository;

import com.degging.be.cafe.entity.CafeEntity;
import org.springframework.data.jpa.repository.JpaRepository;

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
}