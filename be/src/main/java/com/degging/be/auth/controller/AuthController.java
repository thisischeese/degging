package com.degging.be.auth.controller;

import com.degging.be.auth.dto.request.*;
import com.degging.be.auth.dto.response.LoginResponse;
import com.degging.be.auth.dto.response.RefreshResponse;
import com.degging.be.auth.dto.response.SignupResponse;
import com.degging.be.auth.service.AuthService;
import com.degging.be.auth.service.VerificationService;
import com.degging.be.global.dto.BaseResponse;
import com.degging.be.global.exception.BaseException;
import com.degging.be.global.exception.errorcode.CommonErrorCode;
import com.degging.be.user.service.MemberService;
import jakarta.validation.Valid;
import lombok.RequiredArgsConstructor;
import org.springframework.security.core.annotation.AuthenticationPrincipal;
import org.springframework.security.core.userdetails.UserDetails;
import org.springframework.web.bind.annotation.*;

import java.util.UUID;

/**
 * 인증 및 회원 관리와 관련된 API를 처리하는 컨트롤러
 *
 * 이메일 인증, 회원가입, 로그인, 토큰 관리 및 비밀번호 제어
 */
@RestController
@RequiredArgsConstructor
@RequestMapping("/api/auth")
public class AuthController {

    private final AuthService authService;
    private final MemberService memberService;
    private final VerificationService verificationService;

    private UUID getUserId(UserDetails user) {
        if (user == null) {
            throw new BaseException(CommonErrorCode.UNAUTHORIZED);
        }
        return UUID.fromString(user.getUsername());
    }

    /**
     * 이메일 인증 코드 발송 요청
     *
     * @param request 인증 코드를 발송할 이메일 정보가 담긴 DTO
     * @return 성공 응답 객체
     */
    @PostMapping("/email/verification/request")
    public BaseResponse<Void> requestVerification(@Valid @RequestBody EmailSendRequest request) {
        verificationService.sendVerificationCode(request.getEmail());
        return BaseResponse.success();
    }

    /**
     * 이메일 인증 코드 확인
     *
     * @param request 이메일과 사용자가 입력한 인증 코드가 담긴 DTO
     * @return 성공 응답 객체
     */
    @PostMapping("/email/verification/confirm")
    public BaseResponse<Void> confirmVerification(@Valid @RequestBody EmailVerifyRequest request) {
        verificationService.confirmVerificationCode(request.getEmail(), request.getCode());
        return BaseResponse.success();
    }

    /**
     * 회원가입 처리
     *
     * @param request 회원가입에 필요한 사용자 정보 DTO
     * @return 회원가입 성공 시 성공 응답 객체
     */
    @PostMapping("/signup")
    public BaseResponse<SignupResponse> signup(@Valid @RequestBody SignupRequest request) {
        SignupResponse response = authService.signUp(request);
        return BaseResponse.success(response);
    }

    /**
     * 이메일과 비밀번호를 기반으로 로그인을 처리
     *
     * @param request 로그인 정보 DTO
     * @return 발급된 토큰 정보를 포함한 성공 응답
     */
    @PostMapping("/login")
    public BaseResponse<LoginResponse> login(@Valid @RequestBody LoginRequest request) {
        LoginResponse response = authService.login(request);
        return BaseResponse.success(response);
    }

    /**
     * 리프레시 토큰을 이용한 액세스 토큰 재발급
     *
     * @param request 리프레시 토큰을 포함한 재발급 요청 DTO
     * @return 재발급된 액세스 토큰을 포함한 성공 응답
     */
    @PostMapping("/reissue")
    public BaseResponse<RefreshResponse> reissue(@Valid @RequestBody RefreshRequest request) {
        RefreshResponse response = authService.reissue(request.getRefreshToken());
        return BaseResponse.success(response);
    }

    /**
     * 로그아웃 처리
     * 현재 인증된 사용자의 리프레시 토큰 무효화
     *
     * @param user 현재 인증된 사용자의 정보
     * @return 성공 응답 객체
     */
    @PostMapping("/logout")

    public BaseResponse<String> logout(@AuthenticationPrincipal UserDetails user) {

        UUID userId = getUserId(user);

        authService.logout(userId);
        return BaseResponse.success();
    }

    /**
     * 비밀번호 찾기
     * 이메일로 임시 비밀번호 전송
     *
     * @param request 비밀번호 찾기 요청 DTO
     * @return 성공 응답 객체
     */
    @PostMapping("/password/find")
    public BaseResponse<Void> findPassword(@Valid @RequestBody FindPasswordRequest request) {
        memberService.findPassword(request.getEmail());
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
