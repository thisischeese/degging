package com.degging.be.global.exception;

import com.degging.be.global.exception.errorcode.ErrorCode;
import lombok.Getter;

/**
 * 프로젝트 전역에서 발생하는 비즈니스 예외 처리 클래스
 *
 * ErrorCode를 내포하여 예외 발생
 * GlobalExceptionHandler에서 공통 에러 응답으로 변환
 */
@Getter
public class BaseException extends RuntimeException{

    // 예외 발생 시 전달하는 에러 코드
    private final ErrorCode errorCode;

    /**
     * ErrorCode 기반으로 BaseException 생성
     *
     * 상위 클래스인 RuntimeException의 생성자에 에러 메시지 전달
     * 예외 발생 시 로그에서 원인 식별
     *
     * @param errorCode 발생한 예외의 종류와 정보를 담고 있는 ErrorCode 객체
     */
    public BaseException(ErrorCode errorCode) {
        super(errorCode.getMessage());
        this.errorCode = errorCode;
    }

}