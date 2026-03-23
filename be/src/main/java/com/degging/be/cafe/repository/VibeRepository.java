package com.degging.be.cafe.repository;

import com.degging.be.cafe.entity.VibeEntity;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;
import org.springframework.stereotype.Repository;

import java.util.List;
import java.util.UUID;

/**
 * 카페 분위기 태그 레포지토리
 */
@Repository
public interface VibeRepository extends JpaRepository<VibeEntity, UUID> {

    // tagIds 에 해당하는 tagName 조회
    @Query("SELECT v.tagName FROM VibeEntity v " +
            "WHERE v.tagId IN :tagIds")
    List<String> findTagNameByTagIds(@Param("tagIds") List<UUID> tagIds);

    // tagNames 에 해당하는 tagId 조회
    @Query("SELECT v.tagId FROM VibeEntity v " +
            "WHERE v.tagName IN :tagNames")
    List<UUID> findTagIdByTagNames(@Param("tagNames") List<String> tagNames);
}
