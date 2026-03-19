package com.degging.be.global.exception.errorcode;

import lombok.AllArgsConstructor;
import lombok.Getter;
import org.springframework.http.HttpStatus;

/**
 * 리뷰(Review) 도메인에서 발생하는 에러 코드 관리
 */
@Getter
@AllArgsConstructor
public enum ReviewErrorCode implements ErrorCode {

    // --- 리뷰 기본 에러 (R100 계열) ---
    REVIEW_NOT_FOUND(HttpStatus.NOT_FOUND, "R101", "존재하지 않는 리뷰입니다."),
    REVIEW_ALREADY_EXISTS(HttpStatus.BAD_REQUEST, "R102", "이미 이 카페에 대한 리뷰를 작성하셨습니다."),
    NOT_REVIEW_AUTHOR(HttpStatus.FORBIDDEN, "R103", "본인이 작성한 리뷰만 수정 또는 삭제할 수 있습니다."),

    // --- 리뷰 본문 및 평점 에러 (R200 계열) ---
    INVALID_RATING_RANGE(HttpStatus.BAD_REQUEST, "R201", "평점은 1점에서 5점 사이여야 합니다."),
    CONTENT_TOO_SHORT(HttpStatus.BAD_REQUEST, "R202", "리뷰 내용은 최소 10자 이상이어야 합니다."),
    CONTENT_TOO_LONG(HttpStatus.BAD_REQUEST, "R203", "리뷰 내용은 최대 500자까지 작성 가능합니다."),

    // --- 리뷰 이미지 관련 에러 (R300 계열) ---
    IMAGE_COUNT_EXCEEDED(HttpStatus.BAD_REQUEST, "R301", "리뷰 이미지는 최대 3장까지 업로드 가능합니다."),
    IMAGE_UPLOAD_FAILED(HttpStatus.INTERNAL_SERVER_ERROR, "R302", "이미지 업로드 중 오류가 발생했습니다."),
    IMAGE_DELETE_FAILED(HttpStatus.INTERNAL_SERVER_ERROR, "R303", "S3 이미지 삭제 중 오류가 발생했습니다."),
    UNSUPPORTED_IMAGE_FORMAT(HttpStatus.BAD_REQUEST, "R304", "지원하지 않는 이미지 형식입니다.(JPG, PNG만 가능)"),
    IMAGE_SIZE_EXCEEDED(HttpStatus.BAD_REQUEST, "R305", "이미지 파일 크기는 10MB를 초과할 수 없습니다.");

    private final HttpStatus status;
    private final String code;
    private final String message;
}