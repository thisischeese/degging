package com.degging.be.cafe.entity;

import com.degging.be.global.entity.BaseEntity;
import jakarta.persistence.*;
import lombok.*;

import java.util.UUID;

/**
 * 분위기 태그 엔티티 클래스
 */
@Entity
@Table(name = "vibe_entities")
@Getter
@Builder
@NoArgsConstructor(access = AccessLevel.PROTECTED)
@AllArgsConstructor
public class VibeEntity extends BaseEntity {

    @Id
    @GeneratedValue(strategy = GenerationType.UUID)
    @Column(name = "tag_id")
    private UUID tagId; // 분위기 태그 ID

    @Column(name = "tag_name", nullable = false, length = 50)
    private String tagName; // 분위기 태그명

}