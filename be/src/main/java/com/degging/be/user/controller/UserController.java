package com.degging.be.user.controller;

import com.degging.be.global.dto.BaseResponse;
import com.degging.be.global.exception.BaseException;
import com.degging.be.global.exception.errorcode.CommonErrorCode;
import com.degging.be.user.dto.request.UserOnboardingRequest;
import com.degging.be.user.dto.request.UserUpdateRequest;
import com.degging.be.user.dto.response.UserDetailResponse;
import com.degging.be.user.service.MemberService;
import com.degging.be.user.service.UserOnboardingService;
import jakarta.validation.Valid;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.security.core.annotation.AuthenticationPrincipal;
import org.springframework.security.core.userdetails.UserDetails;
import org.springframework.web.bind.annotation.*;

import java.util.UUID;

/**
 * 유저와 관련된 요청을 처리하는 컨트롤러
 */
@Slf4j
@RestController
@RequiredArgsConstructor
@RequestMapping("/api/users")
public class UserController {

    private final MemberService memberService;
    private final UserOnboardingService onboardingService;

    private UUID getUserId(UserDetails user) {
        if (user == null) {
            throw new BaseException(CommonErrorCode.UNAUTHORIZED);
        }
        return UUID.fromString(user.getUsername());
    }

    /**
     * 임시 토큰을 가진 유저의 온보딩 선택 결과를 수집
     *
     * @param userId 인증 객체로 부터 추출된 유저
     * @param request 선택한 카페 및 디저트 ID 리스트
     * @return 수집 성공 여부 응답
     */
    @PostMapping("/onboarding")
    public BaseResponse<String> collectOnboarding(
            @AuthenticationPrincipal UUID userId,
            @Valid @RequestBody UserOnboardingRequest request) {

        // 온보딩 분석 및 MongoDB 적재 수행
        onboardingService.processOnboarding(userId, request);

        return BaseResponse.success();
    }

    /**
     * 특정 회원 정보(내정보)를 조회하는 메서드
     * 
     * @param user 인증 객체로 부터 추출된 유저
     * @return 200, UserDetailResponse (해당 회원 정보)
     */
    @GetMapping
    public BaseResponse<UserDetailResponse> getUserDetail(
            @AuthenticationPrincipal UserDetails user){
        UUID userId = getUserId(user);
        UserDetailResponse result = memberService.getUserDetail(userId);
        return BaseResponse.success(result);
    }

    /**
     * 특정 회원 정보를 수정하는 메서드
     *
     * @param request 프로필 이미지, 닉네임
     * @param user 인증 객체로 부터 추출된 유저
     * @return 200
     */
    @PatchMapping
    public BaseResponse<?> updateUser(
            @RequestBody @Valid UserUpdateRequest request,
            @AuthenticationPrincipal UserDetails user){
        UUID userId = getUserId(user);
        memberService.updateUser(userId, request);
        return BaseResponse.success();
    }

    /**
     * 특정 회원을 삭제하는 메서드
     *
     * @param user 인증 객체로 부터 추출된 유저
     * @return 200
     */
    @DeleteMapping
    public BaseResponse<?> removeUser(
            @AuthenticationPrincipal UserDetails user){
        UUID userId = getUserId(user);
        memberService.removeUser(userId);
        return BaseResponse.success();
    }
}