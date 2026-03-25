package com.degging.be.user.dto.request;

import jakarta.validation.constraints.NotBlank;
import lombok.*;
import org.springframework.web.multipart.MultipartFile;

/**
 * 회원 정보 수정 요청 DTO
 */
@Setter
@Getter
@AllArgsConstructor
@NoArgsConstructor
@Builder
public class UserUpdateRequest {
    @NotBlank
    private String nickname;
    private MultipartFile profileImage; // 프로필 이미지 수정 가능, [사진 선택] 시 담겨옴
    private boolean defaultImage; // [기본 이미지] 일 경우 true
 }
