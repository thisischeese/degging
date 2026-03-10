package com.degging.be.cafe.repository;

import com.degging.be.cafe.entity.CafeEntity;
import org.springframework.data.jpa.repository.JpaRepository;

import java.util.UUID;

public interface CafeRepository extends JpaRepository<CafeEntity, UUID> {
}
