package com.degging.be.user.repository;

import com.degging.be.user.entity.UserEntity;
import org.springframework.data.jpa.repository.JpaRepository;

import java.util.Collection;
import java.util.List;
import java.util.Optional;
import java.util.UUID;

/**
 * User 엔티티에 대한 데이터베이스 접근 기능을 담당하는 Repository 인터페이스
 */
public interface UserRepository extends JpaRepository<UserEntity, UUID> {

    // 이메일로 사용자 정보 조회 (로그인 시 사용)
    Optional<UserEntity> findByEmail(String email);

    // 여러 이메일로 사용자 목록 한꺼번에 조회 (크롤링 최적화용)
    List<UserEntity> findAllByEmailIn(Collection<String> emails);

    // 이메일 중복 여부 확인
    boolean existsByEmail(String email);

    // 특정 그룹(A, B)의 사용자 수를 카운트
    long countByAbGroup(Character abGroup);


}