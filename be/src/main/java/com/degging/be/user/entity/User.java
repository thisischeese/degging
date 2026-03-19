package com.degging.be.user.entity;

import com.degging.be.global.entity.BaseEntity;
import jakarta.persistence.*;
import lombok.*;

import java.time.LocalDate;
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
public class User extends BaseEntity {

    @Id
    @GeneratedValue(strategy = GenerationType.UUID)
    @Column(name = "user_id", updatable = false, nullable = false)
    private UUID userId;

    @Column(nullable = false, unique = true, length = 50)
    private String email;

    @Column(nullable = false, length = 255)
    private String password;

    @Column(nullable = false, unique = true)
    private String nickname;

    @Enumerated(EnumType.STRING)
    @Column(nullable = false)
    private Gender gender;

    @Column(nullable = false)
    private LocalDate birthDate;

    @Column(name = "ab_group", length = 1)
    private Character abGroup;

    /**
     * 유저 생성을 위한 정적 팩토리 메서드
     *
     * @param email 유저 이메일
     * @param password 암호화된 비밀번호
     * @param nickname 닉네임
     * @param gender 성별
     * @param birthDate 생년월일
     * @return 생성된 유저 엔티티
     */
    public static User of(String email, String password, String nickname, Gender gender, LocalDate birthDate, Character abGroup) {
        return User.builder()
                .email(email)
                .password(password)
                .nickname(nickname)
                .gender(gender)
                .birthDate(birthDate)
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