package com.degging.be.cafe.repository;

import com.degging.be.cafe.entity.CafeEntity;
import com.degging.be.cafe.entity.CafeVibeTagEntity;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

@Repository
public interface CafeVibeTagRepository extends JpaRepository<CafeVibeTagEntity, Long> {
    void deleteAllByCafe(CafeEntity cafe);
}
