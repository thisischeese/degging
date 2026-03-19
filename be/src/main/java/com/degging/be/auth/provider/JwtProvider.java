package com.degging.be.auth.provider;

import com.degging.be.global.exception.BaseException;
import com.degging.be.global.exception.errorcode.AuthErrorCode;
import io.jsonwebtoken.*;
import io.jsonwebtoken.io.Decoders;
import io.jsonwebtoken.security.Keys;
import io.jsonwebtoken.security.SignatureException;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.security.authentication.UsernamePasswordAuthenticationToken;
import org.springframework.security.core.Authentication;
import org.springframework.security.core.userdetails.UserDetails;
import org.springframework.security.core.userdetails.UserDetailsService;
import org.springframework.stereotype.Component;

import javax.crypto.SecretKey;
import java.time.Instant;
import java.util.Date;
import java.util.UUID;

/**
 * JWT 토큰의 생성, 검증 및 인증 객체 조회를 담당하는 Provider 클래스
 */
@Slf4j
@Component
public class JwtProvider {

    // JWT 서명에 사용할 비밀키
    private final SecretKey secretKey;

    // 토큰 발급자 정보
    private final String issuer;

    // Access Token 만료 시간 (초 단위)
    private final Long accessTokenExpTime;

    // Refresh Token 만료 시간 (초 단위)
    private final Long refreshTokenExpTime;

    // 온보딩용 Temporary Token 만료 시간 (초 단위)
    private final Long tempTokenExpTime;

    // 사용자 정보를 조회하기 위한 서비스
    private final UserDetailsService userDetailsService;

    /**
     * JwtProvider 생성자
     * 설정 파일(application.yml)로부터 값을 주입받아 초기화
     *
     * @param key Base64로 인코딩된 비밀키
     * @param issuer 토큰 발급자
     * @param accessTokenExpTime Access Token 만료 시간
     * @param refreshTokenExpTime Refresh Token 만료 시간
     *
     * @param userDetailsService 사용자 정보 서비스
     */
    public JwtProvider(@Value("${spring.jwt.secret-key}") String key,
                       @Value("${spring.jwt.issuer}") String issuer,
                       @Value("${spring.jwt.access-expiration}") Long accessTokenExpTime,
                       @Value("${spring.jwt.refresh-expiration}") Long refreshTokenExpTime,
                       @Value("${spring.jwt.temp-expiration}") Long tempTokenExpTime,
                       UserDetailsService userDetailsService) {
        this.secretKey = Keys.hmacShaKeyFor(Decoders.BASE64.decode(key));
        this.issuer = issuer;
        this.accessTokenExpTime = accessTokenExpTime;
        this.refreshTokenExpTime = refreshTokenExpTime;
        this.tempTokenExpTime = tempTokenExpTime;
        this.userDetailsService = userDetailsService;
    }

    /**
     * 사용자 식별자(UUID)를 기반으로 Access Token 생성
     *
     * JWT subject에 사용자 UUID 저장
     * 이후 인증 과정에서 subject 값을 기반으로 사용자 정보 조회
     *
     * @param userId 사용자 식별자
     * @return 생성된 Access Token 문자열
     */
    public String createAccessToken(UUID userId) {
        return Jwts.builder()
                .subject(userId.toString())
                .issuer(issuer)
                .issuedAt(Date.from(Instant.now()))
                .expiration(Date.from(Instant.now().plusSeconds(accessTokenExpTime)))
                .signWith(secretKey)
                .compact();
    }

    public String createRefreshToken(UUID userId) {
        Date now = new Date();
        return Jwts.builder()
                .subject(userId.toString())
                .issuedAt(now)
                .expiration(new Date(now.getTime() + refreshTokenExpTime))
                .signWith(secretKey)
                .compact();
    }

    /**
     * 온보딩 진행을 위한 10분 만료 임시 토큰 생성
     *
     * @param userId 사용자 식별자
     * @return 생성된 임시 JWT 토큰
     */
    public String createTemporaryToken(UUID userId) {
        return Jwts.builder()
                .subject(userId.toString())
                .issuer(issuer)
                .claim("type", "ONBOARDING") // 온보딩 전용 클레임
                .issuedAt(Date.from(Instant.now()))
                .expiration(Date.from(Instant.now().plusMillis(tempTokenExpTime))) // 밀리초 단위 가산
                .signWith(secretKey)
                .compact();
    }

    /**
     * JWT 토큰으로부터 Spring Security 인증 객체 생성
     *
     * 토큰 내부 subject에 저장된 사용자 UUID 기반으로
     * CustomUserDetailsService를 통해 사용자 정보 조회
     * Spring Security 인증 객체 생성
     *
     * @param token JWT 토큰
     * @return 인증 객체
     */
    public Authentication getAuthentication(String token) {
        Claims claims = parseClaims(token);
        UserDetails userDetails = userDetailsService.loadUserByUsername(claims.getSubject());
        return new UsernamePasswordAuthenticationToken(userDetails, "", userDetails.getAuthorities());
    }

    /**
     * 전달받은 토큰의 유효성 검증
     * 검증 실패 시 각 상황(만료, 변조, 형식 오류 등)에 맞는 BaseException 발생
     *
     * @param token 검증할 JWT 토큰
     * @return 유효한 토큰일 경우 true
     * @throws BaseException 토큰 만료(TOKEN_EXPIRED), 유효하지 않은 경우(TOKEN_INVALID, TOKEN_MALFORMED)
     */
    public boolean validateToken(String token) {
        try {
            Jwts.parser().verifyWith(secretKey).build().parseSignedClaims(token);
            return true;
        } catch (ExpiredJwtException e) {
            log.error("만료된 JWT 토큰입니다.");
            throw new BaseException(AuthErrorCode.TOKEN_EXPIRED);
        } catch (MalformedJwtException e){
            log.error("잘못된 형식의 JWT 토큰입니다.");
            throw new BaseException(AuthErrorCode.TOKEN_MALFORMED);
        } catch (SignatureException e) {
            log.error("변조된 JWT 토큰입니다.");
            throw new BaseException(AuthErrorCode.TOKEN_INVALID);
        } catch (UnsupportedJwtException e) {
            log.error("지원되지 않는 JWT 토큰입니다.");
            throw new BaseException(AuthErrorCode.TOKEN_INVALID);
        } catch (Exception e) {
            log.error("JWT 토큰 검증 중 예상치 못한 오류가 발생했습니다.");
            throw new BaseException(AuthErrorCode.UNAUTHORIZED_PROCESS);
        }
    }

    /**
     * 토큰 내부의 Claims 정보 파싱
     *
     * @param token JWT 토큰
     * @return 파싱된 Claims 객체
     */
    public Claims parseClaims(String token) {
        return Jwts.parser()
                .verifyWith(secretKey)
                .build()
                .parseSignedClaims(token)
                .getPayload();
    }

}
