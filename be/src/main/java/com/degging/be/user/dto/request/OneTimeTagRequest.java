package com.degging.be.user.dto.request;

import jakarta.validation.constraints.NotEmpty;
import lombok.Getter;
import lombok.NoArgsConstructor;

import java.util.List;

/**
 * 일회성 취향 태그 설정을 위한 요청 DTO
 */
@Getter
@NoArgsConstructor
public class OneTimeTagRequest {

    @NotEmpty(message = "최소 하나 이상의 태그를 선택해야 합니다.")
    private List<String> tags;

}
