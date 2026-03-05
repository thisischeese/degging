package com.degging.be.global.exception.errorcode;

import lombok.AllArgsConstructor;
import lombok.Getter;
import org.springframework.http.HttpStatus;

/**
 * Rank 도메인에서 사용하는 에러 코드
 *
 * HTTP 상태 코드, 커스텀 에러 코드, 에러 메시지 관리
 * BaseException, GlobalExceptionHandler와 연동되어 일관된 응답 제공
 */
@Getter
@AllArgsConstructor
public enum RankErrorcode implements ErrorCode{
    // 랭킹 데이터 초기화 관련 (500)
    RANKING_INIT_FAILED(HttpStatus.INTERNAL_SERVER_ERROR, "R001", "랭킹 데이터 초기 적재 중 오류가 발생했습니다."),
    CSV_FILE_NOT_FOUND(HttpStatus.INTERNAL_SERVER_ERROR, "R002", "랭킹 초기화용 CSV 파일을 찾을 수 없습니다."),

    // 랭킹 조회 및 반영 관련 (500)
    RANKING_PROCESS_ERROR(HttpStatus.INTERNAL_SERVER_ERROR, "R003", "실시간 랭킹 처리 중 내부 오류가 발생했습니다."),
    REDIS_CONNECTION_FAILURE(HttpStatus.INTERNAL_SERVER_ERROR, "R004", "레디스 서버 연결에 실패했습니다.");

    // 응답으로 반환할 HTTP 상태 코드
    private final HttpStatus status;

    // 프론트엔드 식별용 커스텀 에러 코드
    private final String code;

    // 클라이언트에 노출할 에러 메세지
    private final String message;
}
