package com.degging.be.auth.dto.request;

import jakarta.validation.constraints.Email;
import jakarta.validation.constraints.NotBlank;
import lombok.Getter;
import lombok.NoArgsConstructor;

/**
 * 인증 번호를 검증하기 위한 요청 데이터 객체
 */
@Getter
@NoArgsConstructor
public class EmailVerifyRequest {

    @NotBlank(message = "이메일은 필수 입력값입니다.")
    @Email(message = "이메일 형식이 올바르지 않습니다.")
    private String email;

    @NotBlank(message = "인증 코드는 필수 입력값입니다.")
    private String code;

}
