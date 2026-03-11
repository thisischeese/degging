package com.degging.be.global.exception.errorcode;

import lombok.AllArgsConstructor;
import lombok.Getter;
import org.springframework.http.HttpStatus;

/**
 * 스크랩 관련 에러 코드를 관리하는 Enum 클래스
 */
@Getter
@AllArgsConstructor
public enum ScrapErrorCode implements ErrorCode{

    // --- 스크랩 자체 관련 (CRUD) ---
    SCRAP_NOT_FOUND(HttpStatus.NOT_FOUND, "S001", "존재하지 않는 스크랩 폴더입니다."),
    SCRAP_ACCESS_DENIED(HttpStatus.FORBIDDEN, "S002", "해당 스크랩에 대한 접근 권한이 없습니다."),
    SCRAP_NAME_DUPLICATED(HttpStatus.CONFLICT, "S003", "이미 동일한 이름의 스크랩 폴더가 존재합니다."),
    SCRAP_LIMIT_EXCEEDED(HttpStatus.BAD_REQUEST, "S004", "생성 가능한 스크랩 폴더 개수를 초과했습니다."),

    // --- 스크랩 내 카페 관련 ---
    CAFE_ALREADY_SCRAPPED(HttpStatus.CONFLICT, "S101", "이미 이 스크랩 폴더에 추가된 카페입니다."),
    CAFE_NOT_IN_SCRAP(HttpStatus.NOT_FOUND, "S102", "해당 스크랩 폴더에 해당 카페가 존재하지 않습니다."),
    CAFE_SCRAP_FAILED(HttpStatus.INTERNAL_SERVER_ERROR, "S103", "카페 스크랩 처리 중 서버 오류가 발생했습니다.");

    // 응답으로 반환할 HTTP 상태 코드
    private final HttpStatus status;

    // 프론트엔드 식별용 커스텀 에러 코드
    private final String code;

    // 클라이언트에 노출할 에러 메세지
    private final String message;
}
