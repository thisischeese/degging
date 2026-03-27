package com.degging.be.curation.dto.request;

import lombok.AllArgsConstructor;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;

/**
 * 큐레이션 미니맵 요청 DTO
 */

@Getter
@Setter
@NoArgsConstructor
@AllArgsConstructor
public class CurationMinimapRequest {
    private String category;
    private String cafeName;
}
