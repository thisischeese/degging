package com.degging.be.cafe.repository;

import com.degging.be.cafe.entity.CafeEntity;
import org.springframework.data.jpa.repository.JpaRepository;

import java.util.UUID;

public interface CafeRepository extends JpaRepository<CafeEntity, UUID> {
    /**
     * TODO:
     * 상가업소번호(bizesId)를 임시로 kakaoPlaceId 컬럼에 저장
     * 이후 카카오 API 매칭 후 실제 kakaoPlaceId로 업데이트할 예정
     */
    boolean existsByKakaoPlaceId(String kakaoPlaceId);

}
