package com.degging.be.review.entity;

import com.degging.be.global.entity.BaseEntity;
import jakarta.persistence.*;
import lombok.*;

import java.util.UUID;

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

    @Column(name = "sort_order", nullable = false) // 순서
    private int sortOrder;

    // sortOrder 업데이트
    public void updateSortOrder(int sortOrder) {
        this.sortOrder = sortOrder;
    }
}