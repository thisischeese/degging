package com.degging.be.user.entity;

import com.degging.be.global.entity.BaseEntity;
import jakarta.persistence.*;
import lombok.*;

import java.time.LocalDate;
import java.util.UUID;

@Entity
@Table(name = "user_profiles")
@Getter
@NoArgsConstructor(access = AccessLevel.PROTECTED)
@AllArgsConstructor
@Builder
public class UserProfileEntity extends BaseEntity {

    @Id
    private UUID userId;

    @MapsId // User 엔티티의 ID를 이 엔티티의 PK로 매핑
    @OneToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "user_id")
    private UserEntity user;

    @Column(nullable = false, unique = true)
    private String nickname;

    @Enumerated(EnumType.STRING)
    @Column(nullable = false)
    private Gender gender;

    @Column(nullable = false)
    private LocalDate birthDate;

    @Column(name = "profile_image_url", length = 255)
    private String profileImageUrl; // 프로필 사진 url

    @Builder.Default
    @Column(name = "is_onboarded", nullable = false)
    private boolean isOnboarded = false; // 선호도 조사 여부

    /**
     * 회원 정보 수정 메서드
     */
    public void updateUser(String nickname, String profileImageUrl) {
        this.nickname = nickname;
        if (profileImageUrl != null && !profileImageUrl.isBlank()){
            this.profileImageUrl = profileImageUrl;
        }
    }

    /**
     *  유저 업데이트 (유저 업데이트 시 사용)
     */
    public void setUser(UserEntity user) {this.user = user;}

    /**
     * 유저 온보딩 여부를 갱신하는 메서드
     */
    public void updateIsOnboarding(){
        this.isOnboarded = true;
    }

}
