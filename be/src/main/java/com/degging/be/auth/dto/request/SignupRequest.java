package com.degging.be.auth.dto.request;

import com.degging.be.user.entity.Gender;
import com.fasterxml.jackson.annotation.JsonFormat;
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
    @Pattern(regexp = "^\\S+$", message = "닉네임에 공백을 포함할 수 없습니다.")
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
    @JsonFormat(pattern = "yyyy.MM.dd")
    private LocalDate birthDate;
}