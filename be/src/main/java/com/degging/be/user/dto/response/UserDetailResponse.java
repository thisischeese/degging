package com.degging.be.user.dto.response;

import com.degging.be.user.entity.Gender;
import com.degging.be.user.entity.UserEntity;
import com.degging.be.user.entity.UserProfileEntity;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Getter;
import lombok.NoArgsConstructor;

import java.time.LocalDate;
import java.util.*;

/**
 * 사용자 상세 조회 응답 DTO
 */
@Getter
@AllArgsConstructor
@NoArgsConstructor
@Builder
public class UserDetailResponse {
    private UUID userId;
    private String email;
    private String nickname;
    private Gender gender;
    private LocalDate birthDate;
    private List<String> preferredTags; // mongoDB 에서 가져온 취향 태그
    private Character abGroup;
    private String profileImageUrl; // 프로필 이미지

    // entity -> dto (password 제외하고 클라이언트에 응답)
    public static UserDetailResponse of(UserEntity entity, UserProfileEntity profileEntity, List<String> tags){
        return UserDetailResponse.builder()
                .userId(entity.getUserId())
                .email(entity.getEmail())
                .nickname(profileEntity.getNickname())
                .gender(profileEntity.getGender())
                .birthDate(profileEntity.getBirthDate())
                .preferredTags(tags)
                .abGroup(entity.getAbGroup())
                .profileImageUrl(profileEntity.getProfileImageUrl())
                .build();
    }
}
