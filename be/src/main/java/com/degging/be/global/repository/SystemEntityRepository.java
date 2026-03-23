package com.degging.be.global.repository;

import com.degging.be.global.entity.SystemEntity;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

@Repository
public interface SystemEntityRepository extends JpaRepository<SystemEntity, String> {
}
