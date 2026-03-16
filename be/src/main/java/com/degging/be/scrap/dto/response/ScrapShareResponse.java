package com.degging.be.scrap.dto.response;

import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Getter;
import lombok.NoArgsConstructor;

/**
 * 스크랩 공유 링크 생성 후 응답하는 DTO
 */
@Getter
@NoArgsConstructor
@AllArgsConstructor
@Builder
public class ScrapShareResponse {
    private String shareLink;
}
