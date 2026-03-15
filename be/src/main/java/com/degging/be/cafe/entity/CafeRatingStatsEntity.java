package com.degging.be.cafe.entity;

import com.degging.be.global.entity.BaseEntity;
import jakarta.persistence.*;
import lombok.*;

import java.util.UUID;

/**
 * 카페 평점 집계 엔티티 클래스
 */
@Entity
@Table(name = "cafe_rating_stats")
@Getter
@Builder
@NoArgsConstructor(access = AccessLevel.PROTECTED)
@AllArgsConstructor
public class CafeRatingStatsEntity extends BaseEntity {

    @Id
    @Column(name = "cafe_id")
    private UUID cafeId;    // 카페 ID

    @MapsId
    @OneToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "cafe_id")
    private CafeEntity cafe;    // 카페

    @Column(nullable = false)
    private int reviewCount;    // 리뷰 수

    @Column(nullable = false)
    private int ratingSum;      // 평가 총합

    private String soloRatio;   // 혼자 방문 비율

    private String dateRatio;   // 데이트 방문 비율

    private String friendsRatio;    // 친구 방문 비율
}