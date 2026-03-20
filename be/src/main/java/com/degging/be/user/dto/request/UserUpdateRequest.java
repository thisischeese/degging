package com.degging.be.user.dto.request;

import jakarta.validation.constraints.NotBlank;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Getter;
import lombok.NoArgsConstructor;

import java.util.UUID;

/**
 * 회원 정보 수정 요청 DTO
 */
@Getter
@AllArgsConstructor
@NoArgsConstructor
@Builder
public class UserUpdateRequest {
    @NotBlank
    private String nickname;
    private String profileImageUrl; // 프로필 이미지 수정 가능
}
