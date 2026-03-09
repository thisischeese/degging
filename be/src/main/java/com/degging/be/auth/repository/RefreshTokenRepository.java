package com.degging.be.auth.repository;

import com.degging.be.auth.entity.RefreshToken;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

import java.util.Optional;
import java.util.UUID;

/**
 * RefreshToken 엔티티에 대한 데이터베이스 액세스를 담당하는 레포지토리 인터페이스
 */
@Repository
public interface RefreshTokenRepository extends JpaRepository<RefreshToken, UUID> {

    // 토큰 문자열을 통해 리프레시 토큰 조회
    Optional<RefreshToken> findByToken(String token);

}