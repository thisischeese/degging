package com.degging.be.auth.filter;

import com.degging.be.auth.provider.JwtProvider;

import jakarta.servlet.FilterChain;
import jakarta.servlet.ServletException;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.servlet.http.HttpServletResponse;

import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;

import org.springframework.security.core.Authentication;
import org.springframework.security.core.context.SecurityContextHolder;
import org.springframework.util.StringUtils;
import org.springframework.web.filter.OncePerRequestFilter;

import java.io.IOException;

/**
 * 모든 요청에서 JWT 토큰 추출하고 유효성을 검증하여 인증 정보를 설정하는 필터 클래스
 */
@Slf4j
@RequiredArgsConstructor
public class JwtAuthenticationFilter extends OncePerRequestFilter {

    private static final String AUTHORIZATION_HEADER = "Authorization";

    private static final String BEARER_PREFIX = "Bearer ";

    private final JwtProvider jwtProvider;

    /**
     * HTTP 요청을 필터링하여 토큰 기반 인증 수행
     * 유효하지 않은 토큰일 경우 JwtProvider에서 BaseException 발생
     */
    @Override
    protected void doFilterInternal(HttpServletRequest request, HttpServletResponse response, FilterChain filterChain)
            throws ServletException, IOException {

        // 요청 헤더에서 토큰 문자열 추출
        String jwt = resolveToken(request);

        // 토큰이 존재하고 유효한지 검증
        if (StringUtils.hasText(jwt) && jwtProvider.validateToken(jwt)) {
            // 인증 객체 생성 및 SecurityContext 저장
            Authentication authentication = jwtProvider.getAuthentication(jwt);
            SecurityContextHolder.getContext().setAuthentication(authentication);
            log.info("인증 정보가 SecurityContext에 저장되었습니다: {}", authentication.getName());
        }

        filterChain.doFilter(request, response);
    }

    /**
     * HttpServletRequest 헤더에서 Bearer 토큰 문자열 파싱
     *
     * @param request HTTP 요청 객체
     * @return 파싱된 토큰 문자열
     */
    private String resolveToken(HttpServletRequest request) {
        String bearerToken = request.getHeader(AUTHORIZATION_HEADER);
        if (StringUtils.hasText(bearerToken) && bearerToken.startsWith(BEARER_PREFIX)) {
            return bearerToken.substring(BEARER_PREFIX.length());
        }
        return null;
    }

}