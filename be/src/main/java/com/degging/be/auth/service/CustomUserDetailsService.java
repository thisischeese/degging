package com.degging.be.auth.service;

import com.degging.be.global.exception.BaseException;
import com.degging.be.user.entity.User;
import com.degging.be.user.repository.UserRepository;
import lombok.RequiredArgsConstructor;
import org.springframework.security.core.userdetails.UserDetails;
import org.springframework.security.core.userdetails.UserDetailsService;
import org.springframework.security.core.userdetails.UsernameNotFoundException;
import org.springframework.stereotype.Service;

import java.util.UUID;

/**
 * Spring Security 인증 과정에서 사용자 정보 조회하는 서비스 클래스
 *
 * AuthService에서 UserDetailsService를 구현하면서 발생하던
 * 순환 참조 문제를 해결하기 위해 사용자 조회 책임을 분리한 클래스
 */
@Service
@RequiredArgsConstructor
public class CustomUserDetailsService implements UserDetailsService {

    private final UserRepository userRepository;

    /**
     * Spring Security 인증 과정에서 사용자 식별자(UUID)를 기반으로 사용자 조회
     *
     * @param subject 사용자 식별자 UUID 문자열
     * @return UserDetails Spring Security에서 사용하는 UserDetails 객체
     * @throws BaseException 존재하지 않는 사용자일 경우 발생 (ErrorCode.USER_NOT_FOUND)
     */
    @Override
    public UserDetails loadUserByUsername(String subject) throws UsernameNotFoundException {

        final UUID userId;

        // JWT subject → UUID 변환
        try {
            userId = UUID.fromString(subject);
        } catch (IllegalArgumentException e) {
            throw new UsernameNotFoundException("유효하지 않은 사용자 식별자입니다.");
        }

        // 사용자 조회
        User user = userRepository.findById(userId)
                .orElseThrow(() -> new UsernameNotFoundException("사용자를 찾을 수 없습니다."));

        // Spring Security에서 사용할 UserDetails 객체 생성
        return org.springframework.security.core.userdetails.User.builder()
                .username(user.getUserId().toString())
                .password(user.getPassword())
                .authorities("ROLE_USER") // 기본 권한 할당
                .build();
    }
}
