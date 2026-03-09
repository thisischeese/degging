package com.degging.be.global.exception.errorcode;

import lombok.AllArgsConstructor;
import lombok.Getter;
import org.springframework.http.HttpStatus;

/**
 * Cafe 도메인에서 사용하는 에러 코드
 *
 * HTTP 상태 코드, 커스텀 에러 코드, 에러 메시지 관리
 * BaseException, GlobalExceptionHandler와 연동되어 일관된 응답 제공
 */
@Getter
@AllArgsConstructor
public enum CafeErrorCode implements ErrorCode {
    // --- 카페 관련 에러 (C100 계열) ---
    CAFE_NOT_FOUND(HttpStatus.NOT_FOUND, "C101", "존재하지 않는 카페입니다."),
    CAFE_DATA_INVALID(HttpStatus.BAD_REQUEST, "C102", "카페 정보가 유효하지 않습니다."),

    // --- 리뷰 관련 에러 (C200 계열) ---
    REVIEW_NOT_FOUND(HttpStatus.NOT_FOUND, "C201", "존재하지 않는 리뷰입니다."),
    REVIEW_ALREADY_EXISTS(HttpStatus.BAD_REQUEST, "C202", "이미 해당 카페에 리뷰를 작성했습니다."),
    INVALID_RATING_RANGE(HttpStatus.BAD_REQUEST, "C203", "평점은 1점에서 5점 사이여야 합니다."),
    REVIEW_CONTENT_TOO_SHORT(HttpStatus.BAD_REQUEST, "C204", "리뷰 내용은 최소 10자 이상이어야 합니다."),

    // --- 리뷰 이미지 관련 에러 ---
    IMAGE_UPLOAD_FAILED(HttpStatus.INTERNAL_SERVER_ERROR, "C205", "이미지 업로드 중 오류가 발생했습니다."),
    IMAGE_COUNT_EXCEEDED(HttpStatus.BAD_REQUEST, "C206", "리뷰 이미지는 최대 3장까지 업로드 가능합니다."),
    UNSUPPORTED_IMAGE_FORMAT(HttpStatus.BAD_REQUEST, "C207", "지원하지 않는 이미지 형식입니다.");

    // 응답으로 반환할 HTTP 상태 코드
    private final HttpStatus status;

    // 프론트엔드 식별용 커스텀 에러 코드
    private final String code;

    // 클라이언트에 노출할 에러 메세지
    private final String message;
}
