package com.degging.be.scrap.repository;

import com.degging.be.scrap.entity.ScrapEntity;
import com.degging.be.scrap.entity.ScrapShareLinkEntity;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

import java.util.Optional;

/**
 * 스크랩 공유 기능 관련 레포지토리
 */
@Repository
public interface ScrapShareLinkRepository extends JpaRepository<ScrapShareLinkEntity, Long> {
    // 특정 스크랩의 활성화된 공유 링크 찾기 (중복 생성 방지)
    Optional<ScrapShareLinkEntity> findByScrapAndIsActiveTrue(ScrapEntity scrap);

    // 공유 링크로 스크랩을 조회할 때 사용할 메서드 (MVP X)
    Optional<ScrapShareLinkEntity> findByTokenAndIsActiveTrue(String token);}
