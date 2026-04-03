package com.degging.be.discovery.dto.response;

import com.degging.be.cafe.entity.CafeEntity;
import com.degging.be.cafe.entity.CafeImageEntity;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Getter;
import lombok.NoArgsConstructor;
import java.util.UUID;
import java.util.Optional;

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
    private String abGroup;

    public static DiscoveryResponse from(CafeEntity cafe, String abGroup) {
        String finalThumbnail = cafe.getThumbnailUrl();

        // 상세 이미지 중 01.jpg 또는 001.jpg 우선 선택
        if (cafe.getImages() != null && !cafe.getImages().isEmpty()) {
            Optional<String> priorityImage = cafe.getImages().stream()
                    .map(CafeImageEntity::getImageUrl)
                    .filter(url -> url != null && (url.endsWith("/01.jpg") || url.endsWith("/001.jpg")))
                    .findFirst();

            if (priorityImage.isPresent()) {
                finalThumbnail = priorityImage.get();
            }
        }

        return DiscoveryResponse.builder()
                .cafeId(cafe.getCafeId())
                .thumbnailUrl(finalThumbnail)
                .abGroup(abGroup)
                .build();
    }
}
