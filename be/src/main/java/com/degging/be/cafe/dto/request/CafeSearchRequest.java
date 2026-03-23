package com.degging.be.cafe.dto.request;

import jakarta.validation.constraints.NotBlank;
import lombok.Getter;
import lombok.NoArgsConstructor;

import java.util.List;

/**
 * 프론트엔드 파라미터 수신용 검색 요청 DTO
 */
@Getter
@NoArgsConstructor
public class CafeSearchRequest {
    private List<String> mood; // 분위기 태그

    @NotBlank(message = "검색어는 필수 입력값입니다.")
    private String keyword;

    private Double latitude;    // 사용자 현재 위도

    private Double longitude;   // 사용자 현재 경도

}
