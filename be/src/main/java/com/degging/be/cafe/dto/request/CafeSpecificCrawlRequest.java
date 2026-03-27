package com.degging.be.cafe.dto.request;

import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;

import java.util.List;

/**
 * 특정 카페 리스트 크롤링 요청 DTO
 */
@Getter
@Setter
@NoArgsConstructor
public class CafeSpecificCrawlRequest {
    
    private String region;
    
    private List<String> cafeNames;
}
