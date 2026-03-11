package com.degging.be.scrap.repository;

import com.degging.be.scrap.entity.ScrapEntity;
import com.degging.be.user.entity.User;
import org.springframework.data.jpa.repository.JpaRepository;

import java.util.List;
import java.util.UUID;

/**
 * 카페 스크랩 데이터 접근을 위한 레포지토리
 */
public interface ScrapRepository extends JpaRepository<ScrapEntity, UUID> {
    // 특정 사용자의 스크랩명 중복 확인
    boolean existsByNameAndUser(String name, User user);

    // 특정 사용자의 스크랩 리스트 조회
    List<ScrapEntity> findAllByUserUserId(User user);
}
