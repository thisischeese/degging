package com.degging.be.discovery.dto.response;

import com.degging.be.cafe.entity.CafeEntity;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Getter;
import lombok.NoArgsConstructor;
import java.util.UUID;

/**
 * 탐색(Discovery) 탭 응답용 DTO
 */
@Getter
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class DiscoveryResponse {

    private UUID cafeId;
    private String thumbnailUrl;

    public static DiscoveryResponse from(CafeEntity cafe) {
        return DiscoveryResponse.builder()
                .cafeId(cafe.getCafeId())
                .thumbnailUrl(cafe.getThumbnailUrl())
                .build();
    }
}