package com.degging.be.scrap.dto.request;

import jakarta.validation.constraints.NotNull;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Getter;
import lombok.NoArgsConstructor;

/**
 * 스크랩 요청 정보를 담는 DTO
 */
@Getter
@NoArgsConstructor
@AllArgsConstructor
@Builder
public class ScrapRequest {
    private String name;

    @NotNull(message = "색상은 필수 입력 값입니다.")
    private String color;
}
