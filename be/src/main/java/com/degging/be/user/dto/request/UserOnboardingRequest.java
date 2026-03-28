package com.degging.be.user.dto.request;

import jakarta.validation.constraints.NotNull;
import jakarta.validation.constraints.Size;
import lombok.AllArgsConstructor;
import lombok.Getter;
import lombok.NoArgsConstructor;

import java.util.List;
import java.util.UUID;

/**
 * 유저 온보딩 선택 결과를 수집하기 위한 요청 DTO
 */
@Getter
@NoArgsConstructor
@AllArgsConstructor
public class UserOnboardingRequest {

    // 회원가입 시 발급된 임시 온보딩 토큰
    @NotNull
    private String onboardingToken;

    // 선택한 카페 ID 리스트 (정확히 3개)
    @NotNull
    @Size(min = 3, max = 3)
    private List<UUID> cafeIds;

    // 선택한 디저트 리스트 (정확히 3개)
    @NotNull
    @Size(min = 3, max = 3)
    private List<String> menuNames;

}