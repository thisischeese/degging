package com.degging.be.review.entity;

import com.degging.be.global.entity.BaseEntity;
import jakarta.persistence.*;
import lombok.*;

import java.util.UUID;

/**
 * 카페 리뷰 이미지 정보를 담는 엔티티
 */
@Entity
@Table(name = "review_images")
@Getter
@NoArgsConstructor(access = AccessLevel.PROTECTED)
@AllArgsConstructor
@Builder
public class ReviewImageEntity extends BaseEntity {
    @Id
    @GeneratedValue(strategy = GenerationType.UUID)
    private UUID imageId;

    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "review_id")
    private ReviewEntity review;

    private String imageUrl;

    // S3에 실제로 저장된 파일명 (예: 7a97b0b7...jpg)
    @Column(nullable = false)
    private String storedName;

    // 원본 파일명 (예: 다운로드 (5).jpg)
    @Column(nullable = false)
    private String originName;

    @Column(name = "sort_order", nullable = false) // 순서
    private int sortOrder;

    // sortOrder 업데이트
    public void updateSortOrder(int sortOrder) {
        this.sortOrder = sortOrder;
    }
}