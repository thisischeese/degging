package com.degging.be.cafe.entity;

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
}
