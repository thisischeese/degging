package com.degging.be.review.entity;

import com.degging.be.global.entity.BaseEntity;
import com.degging.be.review.dto.request.ReviewUpdateRequest;
import jakarta.persistence.Entity;
import jakarta.persistence.Id;
import com.degging.be.user.entity.User;

import java.util.ArrayList;
import java.util.List;
import java.util.UUID;
import jakarta.persistence.*;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Getter;
import lombok.NoArgsConstructor;

@Entity
@Table(name = "cafe_reviews")
@Getter
@NoArgsConstructor
@AllArgsConstructor
@Builder
public class ReviewEntity extends BaseEntity {

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

    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "user_id", nullable = false)
    private User user;

    @OneToMany(mappedBy = "review", cascade = CascadeType.ALL, orphanRemoval = true)
    private List<ReviewImageEntity> reviewImages = new ArrayList<>();

    @Column(nullable = false)
    private Short rating; // smallint

    @Column(columnDefinition = "TEXT", nullable = false)
    private String content;

    // content, rating 업데이트 로직
    public void update(ReviewUpdateRequest entity) {
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