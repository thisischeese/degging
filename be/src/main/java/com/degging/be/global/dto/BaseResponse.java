package com.degging.be.global.dto;

import lombok.AllArgsConstructor;
import lombok.Getter;

/**
 * 프로젝트 전역에서 사용하는 공통 응답 규격
 *
 * 성공과 실패 여부, 메시지, 결과 데이터를 포함
 * 클라이언트와 일관된 데이터 포맷으로 소통
 *
 * @param <T> 응답 데이터의 타입
 */
@Getter
@AllArgsConstructor
public class BaseResponse<T> {

    private String status;  // "success" 또는 "fail"
    private String code;    // 커스텀 에러 코드
    private String message; // 응답 메시지
    private T data;         // 실제 데이터

    /**
     * 성공 응답 생성 (데이터 포함)
     *
     * @param data 클라이언트에 전달할 결과 데이터
     * @return 성공 상태의 BaseResponse 객체
     */
    public static <T> BaseResponse<T> success(T data) {
        return new BaseResponse<>("success", "200", "요청이 성공적으로 처리되었습니다.", data);
    }

    /**
     * 성공 응답 생성 (데이터 미포함)
     *
     * @return 성공 상태의 BaseResponse 객체
     */
    public static <T> BaseResponse<T> success() {
        return new BaseResponse<>("success", "200", "요청이 성공적으로 처리되었습니다.", null);
    }

    /**
     * 실패 응답을 생성합니다.
     *
     * @param code 에러 식별을 위한 커스텀 코드 (예: C001)
     * @param message 클라이언트에 노출할 에러 메시지
     * @return 실패 상태의 BaseResponse 객체
     */
    public static <T> BaseResponse<T> error(String code, String message) {
        return new BaseResponse<>("fail", code, message, null);
    }

}
