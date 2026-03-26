package com.degging.be.user.repository.mongodb;

import com.degging.be.user.entity.mongodb.UserOnboarding;
import org.springframework.data.mongodb.repository.MongoRepository;

import java.util.Optional;
import java.util.UUID;

/**
 * MongoDB에 저장되는 유저 온보딩 정보를 관리하는 레포지토리
 */
public interface UserOnboardingRepository extends MongoRepository<UserOnboarding, String> {
    // 특정 유저의 데이터 조회 (취향 태그 추출용)
    Optional<UserOnboarding> findByUserId(String userId);
}