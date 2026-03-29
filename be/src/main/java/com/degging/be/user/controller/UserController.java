package com.degging.be.user.controller;

import com.degging.be.auth.dto.request.ResetPasswordRequest;
import com.degging.be.global.dto.BaseResponse;
import com.degging.be.global.exception.BaseException;
import com.degging.be.global.exception.errorcode.CommonErrorCode;
import com.degging.be.user.dto.request.OneTimeTagRequest;
import com.degging.be.user.dto.request.UserOnboardingRequest;
import com.degging.be.user.dto.request.UserUpdateRequest;
import com.degging.be.user.dto.response.UserDetailResponse;
import com.degging.be.user.service.MemberService;
import com.degging.be.user.service.UserOnboardingService;
import jakarta.validation.Valid;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.http.MediaType;
import org.springframework.security.core.annotation.AuthenticationPrincipal;
import org.springframework.security.core.userdetails.UserDetails;
import org.springframework.web.bind.annotation.*;

import java.util.List;
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
     * @param userIdStr 온보딩 토큰에서 추출된 유저 ID 문자열
     * @param request   선택한 카페 및 디저트 ID 리스트
     * @return 수집 성공 여부 응답
     */
    @PostMapping("/onboarding")
    public BaseResponse<String> collectOnboarding(
            @AuthenticationPrincipal String userIdStr,
            @Valid @RequestBody UserOnboardingRequest request) {

        UUID userId = UUID.fromString(userIdStr);

        // 온보딩 분석 및 MongoDB 적재 수행
        onboardingService.processOnboarding(userId, request);

        return BaseResponse.success();
    }

    /**
     * 사용자의 현재 취향 태그 목록 조회 (영구 + 임시 병합)
     *
     * @param user 인증 객체로 부터 추출된 유저
     * @return 취향 태그 리스트
     */
    @GetMapping("/preferences")
    public BaseResponse<List<String>> getUserPreference(
            @AuthenticationPrincipal UserDetails user) {

        UUID userId = getUserId(user);
        List<String> tags = memberService.getUserPreferred(userId);

        return BaseResponse.success(tags);
    }

    /**
     * 사용자가 추가적으로 더 사용하고 싶은 임시 취향 태그 수집 (+ 버튼)
     * 24시간 동안 유지됨
     *
     * @param user    인증 객체로 부터 추출된 유저
     * @param request 선택한 임시 태그 리스트
     * @return 수집 성공 여부 응답
     */
    @PostMapping("/tags/temporary")
    public BaseResponse<String> collectTemporaryTags(
            @AuthenticationPrincipal UserDetails user,
            @Valid @RequestBody OneTimeTagRequest request) {

        UUID userId = getUserId(user);
        memberService.saveTemporaryTags(userId, request.getTags());

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
            @AuthenticationPrincipal UserDetails user) {
        UUID userId = getUserId(user);
        UserDetailResponse result = memberService.getUserDetail(userId);
        return BaseResponse.success(result);
    }

    /**
     * 특정 회원 정보를 수정하는 메서드
     *
     * @param request 프로필 이미지, 닉네임
     * @param user    인증 객체로 부터 추출된 유저
     * @return 200
     */
    @PatchMapping(consumes = MediaType.MULTIPART_FORM_DATA_VALUE)
    public BaseResponse<?> updateUser(
            @ModelAttribute @Valid UserUpdateRequest request,
            @AuthenticationPrincipal UserDetails user) {
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
            @AuthenticationPrincipal UserDetails user) {
        UUID userId = getUserId(user);
        memberService.removeUser(userId);
        return BaseResponse.success();
    }

    /**
     * 비밀번호 재설정
     * 로그인한 사용자가 본인의 비밀번호를 변경
     *
     * @param user 현재 인증된 사용자의 정보
     * @return 성공 응답 객체
     */
    @PatchMapping("/password/reset")
    public BaseResponse<Void> resetPassword(
            @AuthenticationPrincipal UserDetails user,
            @Valid @RequestBody ResetPasswordRequest request) {

        UUID userId = getUserId(user);

        memberService.resetPassword(userId, request);
        return BaseResponse.success();
    }
}