package com.degging.be.auth.dto.request;

import jakarta.validation.constraints.Email;
import jakarta.validation.constraints.NotBlank;
import lombok.Getter;
import lombok.NoArgsConstructor;

/**
 * 이메일 인증 번호 발송 요청 시 사용하는 데이터 객체
 */
@Getter
@NoArgsConstructor
public class EmailSendRequest {

    @NotBlank(message = "이메일은 필수 입력값입니다.")
    @Email(message = "이메일 형식이 올바르지 않습니다.")
    private String email;

}
