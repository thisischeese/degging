package com.degging.be.review.repository;

import com.degging.be.review.entity.ReviewImageEntity;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

import java.util.UUID;

@Repository
public interface ReviewImageRepository extends JpaRepository<ReviewImageEntity, UUID> {
}
