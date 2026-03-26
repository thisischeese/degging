package com.degging.be.cafe.repository;

import com.degging.be.cafe.entity.CafeBusinessHoursEntity;
import com.degging.be.cafe.entity.CafeEntity;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

import java.util.UUID;

@Repository
public interface CafeBusinessHoursRepository extends JpaRepository<CafeBusinessHoursEntity, UUID> {
    void deleteByCafe(CafeEntity cafe);
}
