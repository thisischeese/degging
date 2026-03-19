package com.degging.be.user.dto.response;

import com.degging.be.user.entity.Gender;
import com.degging.be.user.entity.User;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Getter;
import lombok.NoArgsConstructor;

import java.time.LocalDate;
import java.util.UUID;

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
    private Character abGroup;

    // entity -> dto (password 제외하고 클라이언트에 응답)
    public static UserDetailResponse from(User entity){
        return UserDetailResponse.builder()
                .userId(entity.getUserId())
                .email(entity.getEmail())
                .nickname(entity.getNickname())
                .gender(entity.getGender())
                .birthDate(entity.getBirthDate())
                .abGroup(entity.getAbGroup())
                .build();
    }
}
