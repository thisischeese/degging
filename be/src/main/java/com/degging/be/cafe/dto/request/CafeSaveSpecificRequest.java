package com.degging.be.cafe.dto.request;

import jakarta.validation.constraints.NotBlank;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;

/**
 * 카카오 검색을 통한 특정 카페 직접 저장 요청 DTO
 */
@Getter
@Setter
@NoArgsConstructor
public class CafeSaveSpecificRequest {
    
    private String region;
    
    @NotBlank(message = "카페 이름은 필수입니다.")
    private String name;
}
