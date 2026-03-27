package com.degging.be.user.repository;

import com.degging.be.user.entity.UserPreferenceEntity;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

import java.util.UUID;

@Repository
public interface UserPreferenceRepository extends JpaRepository<UserPreferenceEntity, UUID> {
}
