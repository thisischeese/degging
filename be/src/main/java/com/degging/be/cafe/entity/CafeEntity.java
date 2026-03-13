package com.degging.be.cafe.entity;

import com.degging.be.cafe.dto.response.StoreListInUpjongItem;
import com.degging.be.global.entity.BaseEntity;
import jakarta.persistence.*;
import lombok.*;
import org.locationtech.jts.geom.Point;

import java.util.UUID;

/**
 * 카페 정보를 저장하는 엔티티 클래스
 *
 * BaseEntity 상속으로 생성/수정 시간 자동 관리
 */
@Entity
@Getter
@Builder
@NoArgsConstructor(access = AccessLevel.PROTECTED)
@AllArgsConstructor
@Table(name = "cafes")
public class CafeEntity extends BaseEntity {

    @Id
    @GeneratedValue(strategy = GenerationType.UUID)
    @Column(updatable = false, nullable = false)
    private UUID cafeId;

    @Column(nullable = false, unique = true)
    private String kakaoPlaceId;

    @Column(nullable = false)
    private String name;    // 상호명

    private String address; // 주소

    private String roadAddress; // 도로명 주소

    private String phone;   // 전화번호

    private String kakaoMapUrl; // 카카오 맵 url

    private String thumbnailUrl; // 썸네일 이미지 url

    @Enumerated(EnumType.STRING)
    @Column(nullable = false)
    private CafeStatus status;  // Enum으로 지정된 영업 상태 (영업/폐업/상태확인불가)

    @Column(columnDefinition = "geography(Point,4326)", nullable = false)
    private Point location; // 카페 위치 PostGIS

    private String cafeIntro;   // 카페 한줄 소개

    private String businessHours;   // 영업 시간

    @Column(nullable = false)
    @Builder.Default
    private boolean franchise = false;  // 프랜차이즈 여부

    /**
     * 상가정보 API 응답 데이터를 기반으로 기본 카페 엔티티 생성
     *
     * 수집 시점에는 상가업소번호(bizesId)를 임시로 kakaoPlaceId에 저장
     * 이후 카카오 API 매칭을 통해 실제 kakaoPlaceId로 업데이트
     *
     * @param item 상가정보 API에서 조회한 업소 데이터
     * @param location 카페 위치 정보 (PostGIS Point)
     * @return 생성된 CafeEntity 객체
     */
    public static CafeEntity from(StoreListInUpjongItem item, Point location) {
        return CafeEntity.builder()
                .kakaoPlaceId(item.getBizesId())
                .name(item.getBizesNm())
                .address(toNullIfBlank(item.getLnoAdr()))
                .roadAddress(toNullIfBlank(item.getRdnmAdr()))
                .phone(null)
                .kakaoMapUrl(null)
                .thumbnailUrl(null)
                .status(CafeStatus.UNKNOWN)
                .location(location)
                .cafeIntro(null)
                .businessHours(null)
                .build();
    }

    /**
     * 문자열이 null이거나 공백이면 null로 변환
     *
     * @param value 변환할 문자열 값
     * @return value가 null 또는 공백이면 null, 그렇지 않으면 원래 문자열 반환
     */
    private static String toNullIfBlank(String value) {
        if (value == null || value.isBlank()) {
            return null;
        }
        return value;
    }

    /**
     * 카카오 API 매칭 결과로 카페 정보를 업데이트한다.
     *
     * @param kakaoPlaceId 카카오 장소 ID
     * @param phone 카카오 API에서 조회한 전화번호
     * @param kakaoMapUrl 카카오 지도 URL
     */
    public void updateKakaoPlaceInfo(String kakaoPlaceId, String phone, String kakaoMapUrl) {
        this.kakaoPlaceId = kakaoPlaceId;
        this.phone = phone;
        this.kakaoMapUrl = kakaoMapUrl;
    }
}
