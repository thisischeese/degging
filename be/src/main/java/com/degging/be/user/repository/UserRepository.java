package com.degging.be.user.repository;

import com.degging.be.user.entity.User;
import org.springframework.data.jpa.repository.JpaRepository;

import java.util.Optional;
import java.util.UUID;

/**
 * User 엔티티에 대한 데이터베이스 접근 기능을 담당하는 Repository 인터페이스
 */
public interface UserRepository extends JpaRepository<User, UUID> {

    // 이메일로 사용자 정보 조회 (로그인 시 사용)
    Optional<User> findByEmail(String email);

    // 이메일 중복 여부 확인
    boolean existsByEmail(String email);
}