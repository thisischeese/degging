package com.degging.be.user.entity;

import com.degging.be.global.entity.BaseEntity;
import com.degging.be.review.entity.ReviewEntity;
import com.degging.be.scrap.entity.ScrapEntity;
import jakarta.persistence.*;
import lombok.*;

import java.util.ArrayList;
import java.util.List;
import java.util.UUID;

/**
 * 서비스 사용자 정보를 저장하는 엔티티 클래스
 *
 * BaseEntity 상속으로 생성/수정 시간 자동 관리
 */
@Entity
@Table(name = "users")
@Getter
@NoArgsConstructor(access = AccessLevel.PROTECTED)
@AllArgsConstructor
@Builder
public class UserEntity extends BaseEntity {

    @Id
    @GeneratedValue(strategy = GenerationType.UUID)
    @Column(name = "user_id", updatable = false, nullable = false)
    private UUID userId;

    @Column(nullable = false, unique = true, length = 100)
    private String email;

    @Column(nullable = false, length = 255)
    private String password;

    @Column(name = "ab_group", length = 1)
    private Character abGroup;

    @OneToOne(mappedBy = "user", cascade = CascadeType.ALL, orphanRemoval = true, fetch = FetchType.LAZY)
    private UserProfileEntity profile;

    @Builder.Default
    @OneToMany(mappedBy = "user", cascade = CascadeType.ALL, orphanRemoval = true)
    private List<ReviewEntity> reviews = new ArrayList<>();

    @Builder.Default
    @OneToMany(mappedBy = "user", cascade = CascadeType.ALL, orphanRemoval = true)
    private List<ScrapEntity> scraps = new ArrayList<>();

    /**
     * 프로필과 유저를 연결하기 위한 메서드
     */
    public void setProfile(UserProfileEntity profile) {
        this.profile = profile;
        if (profile.getUser() != this) {
            profile.setUser(this);
        }
    }

    /**
     * 유저 생성을 위한 정적 팩토리 메서드
     *
     * @param email 유저 이메일
     * @param password 암호화된 비밀번호
     * @return 생성된 유저 엔티티
     */
    public static UserEntity of(String email, String password, Character abGroup) {
        return UserEntity.builder()
                .email(email)
                .password(password)
                .abGroup(abGroup)
                .build();
    }

    /**
     * 비밀번호 변경을 위한 메서드
     *
     * @param encodedPassword 변경하려는 인코딩된 비밀번호
     */
    public void updatePassword(String encodedPassword) {
        this.password = encodedPassword;
    }
}