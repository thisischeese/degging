package com.degging.be.auth.service;

import com.degging.be.auth.entity.RefreshToken;
import com.degging.be.auth.dto.request.LoginRequest;
import com.degging.be.auth.dto.response.LoginResponse;
import com.degging.be.auth.dto.response.RefreshResponse;
import com.degging.be.auth.provider.JwtProvider;
import com.degging.be.auth.repository.RefreshTokenRepository;
import com.degging.be.global.exception.BaseException;
import com.degging.be.global.exception.errorcode.AuthErrorCode;

import com.degging.be.global.exception.errorcode.UserErrorCode;
import com.degging.be.user.entity.User;
import com.degging.be.user.repository.UserRepository;

import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.security.core.userdetails.UserDetails;
import org.springframework.security.core.userdetails.UserDetailsService;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.util.UUID;

/**
 * 인증 관련 비즈니스 로직을 처리하고 Spring Security의 사용자 정보를 로드하는 서비스 클래스
 */
@Slf4j
@Service
@RequiredArgsConstructor
@Transactional(readOnly = true)
public class AuthService implements UserDetailsService {

    private final UserRepository userRepository;
    private final RefreshTokenRepository refreshTokenRepository;
    private final PasswordEncoder passwordEncoder;
    private final JwtProvider jwtProvider;

    /**
     * Spring Security 인증 과정에서 사용자 식별자(UUID)를 기반으로 사용자 조회
     *
     * @param subject 사용자 식별자 UUID 문자열
     * @return UserDetails Spring Security에서 사용하는 UserDetails 객체
     * @throws BaseException 존재하지 않는 사용자일 경우 발생 (ErrorCode.USER_NOT_FOUND)
     */
    @Override
    public UserDetails loadUserByUsername(String subject) {

        UUID userId = UUID.fromString(subject);

        // 사용자 확인
        User user = userRepository.findById(userId)
                .orElseThrow(() -> new BaseException(UserErrorCode.USER_NOT_FOUND));

        return org.springframework.security.core.userdetails.User.builder()
                .username(user.getUserId().toString())
                .password(user.getPassword())
                .authorities("ROLE_USER") // 기본 권한 할당
                .build();
    }

    /**
     * 사용자의 이메일과 비밀번호를 검증 후 액세스 토큰 발급
     *
     * @param request 로그인 정보 DTO
     * @return LoginResponse 생성된 액세스 토큰을 포함한 LoginResponse
     * @throws BaseException 사용자가 없거나 비밀번호가 틀린 경우 발생
     */
    @Transactional
    public LoginResponse login(LoginRequest request) {

        // 이메일 존재 확인
        User user = userRepository.findByEmail(request.getEmail())
                .orElseThrow(() -> new BaseException(UserErrorCode.USER_NOT_FOUND));

        // 비밀번호 일치 여부 확인
        if (!passwordEncoder.matches(request.getPassword(), user.getPassword())) {
            throw new BaseException(UserErrorCode.PASSWORD_INVALID);
        }

        // 토큰 생성
        String accessToken = jwtProvider.createAccessToken(user.getUserId());
        String refreshToken = jwtProvider.createRefreshToken(user.getUserId());

        RefreshToken tokenEntity = new RefreshToken(user.getUserId(), refreshToken);
        refreshTokenRepository.save(tokenEntity);

        return LoginResponse.of(accessToken, refreshToken);
    }

    /**
     * 리프레시 토큰을 사용하여 새로운 액세스 토큰을 재발급
     *
     * @param refreshToken 클라이언트로부터 전달받은 리프레시 토큰
     * @return RefreshResponse 새롭게 발급된 액세스 토큰을 담은 RefreshResponse DTO
     * @throws BaseException 유효하지 않거나 존재하지 않는 토큰일 경우 발생
     */
    @Transactional
    public RefreshResponse reissue(String refreshToken) {
        // refreshToken 유효성 및 만료 여부 검증
        jwtProvider.validateToken(refreshToken);

        // DB에서 Refresh Token 검색
        RefreshToken savedToken = refreshTokenRepository.findByToken(refreshToken)
                .orElseThrow(() -> new BaseException(AuthErrorCode.TOKEN_INVALID));

        // 새로운 Access Token 발급
        String newAccessToken = jwtProvider.createAccessToken(savedToken.getUserId());

        return RefreshResponse.of(newAccessToken);
    }

    /**
     * 사용자의 리프레시 토큰을 삭제하여 로그아웃 처리 & SSE 연결 정리
     *
     * @param userId 사용자의 식별자 (UUID)
     */
    @Transactional
    public void logout(UUID userId) {
        // 해당 유저의 리프레시 토큰이 존재하면 삭제
        refreshTokenRepository.deleteById(userId);
    }

}