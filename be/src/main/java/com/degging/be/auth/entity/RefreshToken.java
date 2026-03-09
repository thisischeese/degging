package com.degging.be.auth.entity;

import jakarta.persistence.*;
import lombok.AccessLevel;
import lombok.Getter;
import lombok.NoArgsConstructor;
import org.hibernate.annotations.JdbcTypeCode;
import org.hibernate.type.SqlTypes;

import java.util.UUID;

/**
 * 사용자의 리프레시 토큰 정보 저장하는 엔티티 클래스
 */
@Entity
@Getter
@NoArgsConstructor(access = AccessLevel.PROTECTED)
@Table(name = "refresh_token")
public class RefreshToken {

    @Id
    @Column(name = "user_id")
    private UUID userId;

    @Column(nullable = false)
    private String token;

    public RefreshToken(UUID userId, String token) {
        this.userId = userId;
        this.token = token;
    }

    public void updateToken(String newToken) {
        this.token = newToken;
    }

}