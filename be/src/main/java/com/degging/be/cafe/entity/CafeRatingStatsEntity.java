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

    // 평점 업데이트 메서드 (리뷰 생성)
    public void updateRating(int newRating){
        this.ratingSum += newRating;
        this.reviewCount++;
    }

    // 크롤링된 통계 데이터 덮어쓰기 메서드
    public void updateCrawledStats(int reviewCount, int ratingSum, String soloRatio, String dateRatio, String friendsRatio) {
        this.reviewCount = reviewCount;
        this.ratingSum = ratingSum;
        this.soloRatio = soloRatio;
        this.dateRatio = dateRatio;
        this.friendsRatio = friendsRatio;
    }

    // 평점 수정 메서드 (리뷰 수정)
    public void modifyRating(int oldRating, int newRating){
        this.ratingSum = this.ratingSum - oldRating + newRating;
    }

    // 평점 삭제 메서드 (리뷰 삭제)
    public void deductRating(int rating) {
        this.ratingSum -= rating;
        this.reviewCount--;
    }

    public static CafeRatingStatsEntity from(CafeEntity cafe){
        return CafeRatingStatsEntity.builder()
                .cafe(cafe)
                .reviewCount(0)
                .ratingSum(0)
                .soloRatio("0")
                .dateRatio("0")
                .friendsRatio("0")
                .build();
    }
}