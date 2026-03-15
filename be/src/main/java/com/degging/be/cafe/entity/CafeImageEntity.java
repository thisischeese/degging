package com.degging.be.cafe.entity;

import com.degging.be.global.entity.BaseEntity;
import jakarta.persistence.*;
import lombok.*;

/**
 * 카페 이미지 엔티티 클래스
 */
@Entity
@Table(name = "cafe_images")
@Getter
@Builder
@NoArgsConstructor(access = AccessLevel.PROTECTED)
@AllArgsConstructor
public class CafeImageEntity extends BaseEntity {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long imageId;   // 이미지 ID

    @Column(nullable = false, length = 255)
    private String imageUrl;    // 이미지 URL

    @Column(nullable = false)
    private int sortOrder;  // 이미지 순서

    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "cafe_id", nullable = false)
    private CafeEntity cafe;    // 카페
}