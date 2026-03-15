package com.degging.be.cafe.entity;

import jakarta.persistence.*;
import lombok.*;

/**
 * 카페 분위기 태그 매핑 엔티티 클래스
 */
@Entity
@Table(name = "cafe_vibe_tags")
@Getter
@Builder
@NoArgsConstructor(access = AccessLevel.PROTECTED)
@AllArgsConstructor
public class CafeVibeTagEntity {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    @Column(name = "cafe_vibe_tag_id")
    private Long cafeVibeTagId; // 카페 분위기 태그 ID

    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "cafe_id", nullable = false)
    private CafeEntity cafe;    // 카페

    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "tag_id", nullable = false)
    private VibeEntity vibe;    // 분위기 태그

}