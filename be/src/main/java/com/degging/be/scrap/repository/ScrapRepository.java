package com.degging.be.scrap.repository;

import com.degging.be.scrap.entity.ScrapEntity;
import org.springframework.data.jpa.repository.JpaRepository;

import java.util.UUID;

/**
 * 카페 스크랩 데이터 접근을 위한 레포지토리
 */
public interface ScrapRepository extends JpaRepository<ScrapEntity, UUID> {
}
