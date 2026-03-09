package com.degging.be.review.entity;

import jakarta.persistence.Entity;
import jakarta.persistence.Id;

import java.util.UUID;
import jakarta.persistence.*;
import lombok.AllArgsConstructor;
import lombok.Getter;
import lombok.NoArgsConstructor;
import org.hibernate.annotations.CreationTimestamp;
import org.hibernate.annotations.UpdateTimestamp;

import java.time.OffsetDateTime;

@Entity
@Table(name = "cafe_reviews")
@Getter
@NoArgsConstructor
@AllArgsConstructor
public class ReviewEntity {

    @Id
    @GeneratedValue(strategy = GenerationType.UUID)
    @Column(name = "review_id", updatable = false, nullable = false)
    private UUID reviewId;

    @Column(name = "cafe_id", nullable = false)
    private UUID cafeId;

    @Column(name = "user_id", nullable = false)
    private UUID userId;
    // TODO : 아직 Entity 받기 전이라 임시로 UUID 로 설정해둠

//    @ManyToOne(fetch = FetchType.LAZY)
//    @JoinColumn(name = "cafe_id", nullable = false)
//    private CafeEntity cafe;
//
//    @ManyToOne(fetch = FetchType.LAZY)
//    @JoinColumn(name = "user_id", nullable = false)
//    private UserEntity user;
//
//    @OneToMany(mappedBy = "review", cascade = CascadeType.ALL, orphanRemoval = true)
//    private List<ReviewImageEntity> reviewImages = new ArrayList<>();

    @Column(nullable = false)
    private short rating; // smallint

    @Column(columnDefinition = "TEXT", nullable = false)
    private String content;

    // S3 URL 저장을 위한 컬럼
    @Column(name = "image_url")
    private String imageUrl;

    @CreationTimestamp // 생성 시 자동 기록
    @Column(name = "created_at", nullable = false, updatable = false)
    private OffsetDateTime createdAt; // timestamptz 와 매핑

    @UpdateTimestamp // 수정 시 자동 기록
    @Column(name = "updated_at", nullable = false)
    private OffsetDateTime updatedAt;

}