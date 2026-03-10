package com.degging.be.global.exception.errorcode;

import lombok.AllArgsConstructor;
import lombok.Getter;
import org.springframework.http.HttpStatus;

/**
 * 인증 및 권한 관련 에러 코드를 관리하는 Enum 클래스
 */
@Getter
@AllArgsConstructor
public enum AuthErrorCode implements ErrorCode{

    // JWT 토큰 관련 에러
    TOKEN_EXPIRED(HttpStatus.UNAUTHORIZED, "A001", "만료된 토큰입니다."),
    TOKEN_INVALID(HttpStatus.UNAUTHORIZED, "A002", "유효하지 않은 토큰입니다."),
    TOKEN_MALFORMED(HttpStatus.UNAUTHORIZED, "A003", "잘못된 형식의 토큰입니다."),
    SIGNATURE_INVALID(HttpStatus.UNAUTHORIZED, "A004", "변조된 토큰입니다."),

    // 인증 실패
    UNAUTHORIZED_PROCESS(HttpStatus.UNAUTHORIZED, "A005", "인증 과정에서 오류가 발생했습니다."),

    // 이메일 인증 관련 에러
    EMAIL_DUPLICATE(HttpStatus.CONFLICT, "A006", "이미 가입된 이메일입니다."),
    VERIFICATION_CODE_EXPIRED(HttpStatus.GONE, "A007", "인증 번호가 만료되었습니다."),
    VERIFICATION_CODE_MISMATCH(HttpStatus.BAD_REQUEST, "A008", "인증 번호가 일치하지 않습니다."),
    EMAIL_NOT_VERIFIED(HttpStatus.FORBIDDEN, "A009", "이메일 인증이 완료되지 않았습니다.");

    // 응답으로 반환할 HTTP 상태 코드
    private final HttpStatus status;

    // 프론트엔드 식별용 커스텀 에러 코드
    private final String code;

    // 클라이언트에 노출할 에러 메세지
    private final String message;
}
