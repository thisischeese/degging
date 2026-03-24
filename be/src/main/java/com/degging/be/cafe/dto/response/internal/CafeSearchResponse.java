package com.degging.be.cafe.dto.response.internal;

import com.degging.be.cafe.entity.CafeEntity;
import lombok.*;

import java.util.List;
import java.util.UUID;

/**
 * 검색에 대한 응답 DTO
 */
@Getter
@Builder
@AllArgsConstructor
@NoArgsConstructor
public class CafeSearchResponse {
    private List<CafeSearchItem> cafes;

    @Getter
    @Builder
    @AllArgsConstructor
    @NoArgsConstructor
    public static class CafeSearchItem {
        private UUID cafeId;
        private String name;
        private String address;
        private Double latitude;
        private Double longitude;
        private Long distance; // 현재 위치와의 거리 (m)
        private String cafeIntro; // 카페 한줄소개
        private String thumbnailUrl;


        // DTO 변환 및 거리 계산 로직을 내부로 이동
        public static CafeSearchItem from(CafeEntity cafe, Double userLat, Double userLon) {
            // PostGIS Point 에서 좌표 추출 (x 경도, y 위도)
            Double cafeLon = cafe.getLocation().getX();
            Double cafeLat = cafe.getLocation().getY();

            double distInMeters = calculateDistanceInMeters(userLat, userLon, cafeLat, cafeLon);

            return CafeSearchItem.builder()
                    .cafeId(cafe.getCafeId())
                    .name(cafe.getName())
                    .address(cafe.getAddress())
                    .latitude(cafeLat)
                    .longitude(cafeLon)
                    .cafeIntro(cafe.getCafeIntro())
                    .distance(Math.round(distInMeters)) // 반올림하여 정수로 저장
                    .thumbnailUrl(cafe.getThumbnailUrl())
                    .build();
        }

        /**
         * 하버사인 공식을 이용한 거리 계산 (m 단위 반환)
         */
        private static double calculateDistanceInMeters(double lat1, double lon1, double lat2, double lon2) {
            double R = 6371e3; // 지구 반지름 (m)
            double phi1 = Math.toRadians(lat1);
            double phi2 = Math.toRadians(lat2);
            double deltaPhi = Math.toRadians(lat2 - lat1);
            double deltaLambda = Math.toRadians(lon2 - lon1);

            double a = Math.sin(deltaPhi / 2) * Math.sin(deltaPhi / 2) +
                    Math.cos(phi1) * Math.cos(phi2) *
                            Math.sin(deltaLambda / 2) * Math.sin(deltaLambda / 2);
            double c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));

            return R * c; // 결과는 미터(m) 단위
        }
    }
}