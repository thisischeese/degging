package com.degging.be.auth.dto.request;

import com.degging.be.user.entity.Gender;
import com.fasterxml.jackson.annotation.JsonFormat;
import com.fasterxml.jackson.databind.annotation.JsonDeserialize;
import com.fasterxml.jackson.datatype.jsr310.deser.LocalDateDeserializer;
import jakarta.validation.constraints.*;
import lombok.Getter;
import lombok.NoArgsConstructor;

import java.time.LocalDate;

/**
 * 회원가입 요청 시 클라이언트로부터 전달받는 데이터 객체
 */
@Getter
@NoArgsConstructor
public class SignupRequest {

    @NotBlank(message = "닉네임은 필수 입력값입니다.")
    @Size(min = 2, max = 10, message = "닉네임은 2자 이상 10자 이하여야 합니다.")
    @Pattern(
            regexp = "^[a-zA-Z0-9가-힣]+$",
            message = "닉네임은 한글, 영문, 숫자만 가능하며 특수문자나 자음/모음 단독 입력은 불가합니다."
    )
    private String nickname;

    @NotBlank(message = "이메일은 필수 입력값입니다.")
    @Email(message = "이메일 형식이 올바르지 않습니다.")
    private String email;

    @NotBlank(message = "비밀번호는 필수 입력값입니다.")
    @Pattern(regexp = "^(?=.*[A-Za-z])(?=.*\\d)(?=.*[@$!%*#?&])[A-Za-z\\d@$!%*#?&]{8,16}$", message = "비밀번호는 8~16자 영문, 숫자, 특수문자를 포함해야 합니다.")
    private String password;

    @NotNull(message = "성별은 필수 입력값입니다.")
    private Gender gender;

    @NotNull(message = "생년월일은 필수 입력값입니다.")
    @Past(message = "생년월일은 과거 날짜여야 합니다.")
    // 역직렬화(String -> LocalDate) 도구 지정
    @JsonDeserialize(using = LocalDateDeserializer.class)
    @JsonFormat(shape = JsonFormat.Shape.STRING, pattern = "yyyy.MM.dd", timezone = "Asia/Seoul")
    private LocalDate birthDate;
}