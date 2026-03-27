package com.degging.be.global.exception.errorcode;

import lombok.AllArgsConstructor;
import lombok.Getter;
import org.springframework.http.HttpStatus;

/**
 * Curation 도메인에서 사용하는 에러 코드
 */

@Getter
@AllArgsConstructor
public enum CurationErrorCode implements ErrorCode {
    
    CURATION_NOT_FOUND(HttpStatus.NOT_FOUND, "CU101", "존재하지 않는 큐레이션 정보입니다."),
    CURATION_CATEGORY_NOT_FOUND(HttpStatus.NOT_FOUND, "CU102", "존재하지 않는 큐레이션 카테고리입니다.");

    private final HttpStatus status;
    private final String code;
    private final String message;
}
