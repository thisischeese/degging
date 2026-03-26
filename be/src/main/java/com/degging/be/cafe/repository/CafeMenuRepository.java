package com.degging.be.cafe.repository;

import com.degging.be.cafe.entity.CafeEntity;
import com.degging.be.cafe.entity.CafeMenuEntity;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

@Repository
public interface CafeMenuRepository extends JpaRepository<CafeMenuEntity, Long> {
    void deleteAllByCafe(CafeEntity cafe);
}
