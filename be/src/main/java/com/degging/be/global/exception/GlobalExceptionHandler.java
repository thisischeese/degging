package com.degging.be.global.exception;

import com.degging.be.global.exception.errorcode.CommonErrorCode;
import com.degging.be.global.exception.errorcode.ErrorCode;
import com.degging.be.global.dto.BaseResponse;
import lombok.extern.slf4j.Slf4j;

import org.springframework.http.ResponseEntity;
import org.springframework.http.converter.HttpMessageNotReadableException;
import org.springframework.web.bind.MethodArgumentNotValidException;
import org.springframework.web.bind.annotation.ExceptionHandler;
import org.springframework.web.bind.annotation.RestControllerAdvice;

/**
 * 전역 예외를 처리하여 공통 응답 포맷으로 변환하는 핸들러 클래스
 *
 * BaseException을 포함한 모든 예외를 가로채어
 * 클라이언트가 이해할 수 있는 규격화된 에러 응답 반환
 */
@Slf4j
@RestControllerAdvice
public class GlobalExceptionHandler {

    /**
     * 비즈니스 로직 중 발생하는 커스텀 예외 처리
     *
     * @param e 프로젝트 기저 예외인 BaseException 객체
     * @return HTTP 상태 코드와 에러 정보가 담긴 ResponseEntity
     */
    @ExceptionHandler(BaseException.class)
    public ResponseEntity<BaseResponse<?>> handleCustomException(BaseException e) {
        ErrorCode errorCode = e.getErrorCode();
        log.error("🚨 CustomException: {} ({})", errorCode.getMessage(), errorCode.getCode());

        return ResponseEntity
                .status(errorCode.getStatus())
                .body(BaseResponse.error(errorCode.getCode(), errorCode.getMessage()));
    }

    /**
     * DTO의 유효성 검사(@Valid) 실패 시 발생하는 예외 처리
     *
     * @AssertTrue 등 검증 어노테이션에 설정된 메시지 추출하여 반환
     * @return 400 에러 상태와 DTO에 정의한 메시지가 담긴 ResponseEntity
     */
    @ExceptionHandler(MethodArgumentNotValidException.class)
    public ResponseEntity<BaseResponse<?>> handleValidationException(MethodArgumentNotValidException e) {
        // 발생한 에러들 중 첫 번째 에러의 기본 메시지 가져옴
        String errorMessage = e.getBindingResult().getAllErrors().get(0).getDefaultMessage();

        log.error("🚨 ValidationException: {}", errorMessage);

        return ResponseEntity
                .status(CommonErrorCode.INVALID_INPUT_VALUE.getStatus())
                .body(BaseResponse.error(CommonErrorCode.INVALID_INPUT_VALUE.getCode(), errorMessage));
    }

    /**
     * JSON 파싱 에러나 Enum 타입 불일치 등 메시지를 읽을 수 없을 때 발생하는 예외 처리
     *
     * @return 400 에러 상태와 공통 메시지가 담긴 ResponseEntity
     */
    @ExceptionHandler(HttpMessageNotReadableException.class)
    public ResponseEntity<BaseResponse<?>> handleHttpMessageNotReadableException(HttpMessageNotReadableException e) {
        log.error("🚨 HttpMessageNotReadableException: {}", e.getMessage());

        return ResponseEntity
                .status(CommonErrorCode.INVALID_INPUT_VALUE.getStatus())
                .body(BaseResponse.error(CommonErrorCode.INVALID_INPUT_VALUE.getCode(), "입력 데이터 형식이 잘못되었습니다."));
    }

    /**
     * 예측하지 못한 시스템 예외 처리
     *
     * @param e 시스템 예외(Exception) 객체
     * @return 500 에러 상태와 공통 서버 에러 메시지가 담긴 ResponseEntity
     */
    @ExceptionHandler(Exception.class)
    public ResponseEntity<BaseResponse<?>> handleException(Exception e) {
        log.error("🚨 Unhandled Exception: ", e);

        return ResponseEntity
                .status(CommonErrorCode.INTERNAL_SERVER_ERROR.getStatus())
                .body(BaseResponse.error(CommonErrorCode.INTERNAL_SERVER_ERROR.getCode(), CommonErrorCode.INTERNAL_SERVER_ERROR.getMessage()));
    }

}
