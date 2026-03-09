package com.degging.be.review.entity;

import com.degging.be.review.dto.request.ReviewUpdateRequestDto;
import jakarta.persistence.Entity;
import jakarta.persistence.Id;

import java.util.ArrayList;
import java.util.List;
import java.util.UUID;
import jakarta.persistence.*;
import lombok.AllArgsConstructor;
import lombok.Builder;
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
@Builder
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
    @OneToMany(mappedBy = "review", cascade = CascadeType.ALL, orphanRemoval = true)
    private List<ReviewImageEntity> reviewImages = new ArrayList<>();

    @Column(nullable = false)
    private Short rating; // smallint

    @Column(columnDefinition = "TEXT", nullable = false)
    private String content;

    @CreationTimestamp // 생성 시 자동 기록
    @Column(name = "created_at", nullable = false, updatable = false)
    private OffsetDateTime createdAt; // timestamptz 와 매핑

    @UpdateTimestamp // 수정 시 자동 기록
    @Column(name = "updated_at", nullable = false)
    private OffsetDateTime updatedAt;

    // content, rating 업데이트 로직
    public void update(ReviewUpdateRequestDto entity) {
        String content = entity.getContent();
        Short rating = entity.getRating();

        // 변경된 내용 수정
        if (content != null && !content.isBlank()) {
            this.content = content;
        }
        if (rating != null) {
            this.rating = rating;
        }
    }
}