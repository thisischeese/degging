package com.degging.be.global.exception.errorcode;

import lombok.Getter;
import lombok.RequiredArgsConstructor;
import org.springframework.http.HttpStatus;

/**
 * User 도메인 관련 에러 코드를 관리하는 Enum 클래스
 */
@Getter
@RequiredArgsConstructor
public enum UserErrorCode implements ErrorCode {

    // 계정 조회 및 로그인
    USER_NOT_FOUND(HttpStatus.NOT_FOUND, "U001", "존재하지 않는 사용자입니다."),
    PASSWORD_INVALID(HttpStatus.UNAUTHORIZED, "U002", "이메일 또는 비밀번호가 일치하지 않습니다."),

    // 비밀번호 변경 및 재설정
    PASSWORD_WRONG(HttpStatus.BAD_REQUEST, "U003", "현재 비밀번호가 일치하지 않습니다."),
    PASSWORD_MISMATCH(HttpStatus.BAD_REQUEST, "U004", "새 비밀번호와 확인 비밀번호가 일치하지 않습니다."),
    SAME_AS_OLD_PASSWORD(HttpStatus.BAD_REQUEST, "U005", "새 비밀번호가 기존 비밀번호와 동일합니다."),

    // 닉네임 중복
    NICKNAME_DUPLICATE(HttpStatus.CONFLICT, "U006", "이미 사용 중인 닉네임입니다."),

    // 온보딩 취향 정보 조회
    ONBOARDING_NOT_FOUND(HttpStatus.NOT_FOUND, "U007", "해당 회원의 온보딩(취향) 정보가 존재하지 않습니다."),

    // 유저 프로필 수정
    PROFILE_IMAGE_UPLOAD_FAILED(HttpStatus.INTERNAL_SERVER_ERROR, "U008", "프로필 이미지 업로드 중 오류가 발생했습니다.");

    // 응답으로 반환할 HTTP 상태 코드
    private final HttpStatus status;

    // 프론트엔드 식별용 커스텀 에러 코드
    private final String code;

    // 클라이언트에 노출할 에러 메세지
    private final String message;
}
