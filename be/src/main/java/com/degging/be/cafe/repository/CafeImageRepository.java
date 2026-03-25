package com.degging.be.cafe.repository;

import com.degging.be.cafe.entity.CafeEntity;
import com.degging.be.cafe.entity.CafeImageEntity;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

@Repository
public interface CafeImageRepository extends JpaRepository<CafeImageEntity, Long> {
    void deleteAllByCafe(CafeEntity cafe);
}
