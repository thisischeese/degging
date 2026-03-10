package com.degging.be.auth.filter;

import com.degging.be.global.dto.BaseResponse;
import com.degging.be.global.exception.BaseException;
import com.degging.be.global.exception.errorcode.AuthErrorCode;
import com.degging.be.global.exception.errorcode.ErrorCode;
import com.fasterxml.jackson.databind.ObjectMapper;
import jakarta.servlet.FilterChain;
import jakarta.servlet.ServletException;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.servlet.http.HttpServletResponse;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.http.MediaType;
import org.springframework.stereotype.Component;
import org.springframework.web.filter.OncePerRequestFilter;

import java.io.IOException;

/**
 * JWT 관련 필터에서 발생하는 예외를 가로채 공통 응답 규격으로 변환
 */
@Slf4j
@Component
@RequiredArgsConstructor
public class JwtExceptionFilter extends OncePerRequestFilter {

    // JSON 변환을 위한 객체 매퍼
    private final ObjectMapper objectMapper;

    /**
     * 필터 실행 중 발생하는 예외를 Catch하여 처리
     *
     * @param request     HTTP 요청 객체
     * @param response    HTTP 응답 객체
     * @param filterChain 다음 필터로 요청을 전달하기 위한 필터 체인
     * @throws ServletException 서블릿 관련 예외 발생 시
     * @throws IOException      입출력 관련 예외 발생 시
     */
    @Override
    protected void doFilterInternal(HttpServletRequest request, HttpServletResponse response, FilterChain filterChain) throws ServletException, IOException {
        try {
            // JwtAuthenticationFilter를 포함한 다음 필터 체인 실행
            filterChain.doFilter(request, response);
        } catch (BaseException e) {
            // 정의된 예외 발생 시 에러 응답 처리
            setErrorResponse(response, e.getErrorCode());
        } catch (Exception e) {
            // 그 외 예상치 못한 시스템 에러 처리
            log.error("필터 계층 내 처리되지 않은 예외 발생: ", e);
            setErrorResponse(response, AuthErrorCode.UNAUTHORIZED_PROCESS);
        }
    }

    /**
     * 클라이언트에 JSON 포맷의 에러 응답을 직접 전송
     *
     * @param response  에러 메시지를 작성할 HTTP 응답 객체
     * @param errorCode 클라이언트에 전달할 구체적인 에러 정보를 담은 Enum
     * @throws IOException 응답 스트림에 메시지 작성 실패 시
     */
    private void setErrorResponse(HttpServletResponse response, ErrorCode errorCode) throws IOException {
        response.setStatus(errorCode.getStatus().value());
        response.setContentType(MediaType.APPLICATION_JSON_VALUE);
        response.setCharacterEncoding("UTF-8");

        // 프로젝트 공통 응답 규격 적용
        BaseResponse<Void> errorResponse = BaseResponse.error(errorCode.getCode(), errorCode.getMessage());

        String body = objectMapper.writeValueAsString(errorResponse);
        response.getWriter().write(body);
    }

}
