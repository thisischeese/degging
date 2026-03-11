package com.degging.be.scrap.entity;

import com.degging.be.global.entity.BaseEntity;
import com.degging.be.user.entity.User;
import jakarta.persistence.Entity;
import jakarta.persistence.Id;
import jakarta.persistence.ManyToOne;
import java.util.UUID;
import jakarta.persistence.*;
import lombok.*;

/**
 * 스크랩 정보를 담는 Entity
 */
@Entity
@Table(name = "scraps")
@Getter
@Builder
@NoArgsConstructor(access = AccessLevel.PROTECTED)
@AllArgsConstructor
public class ScrapEntity extends BaseEntity {

    @Id
    @GeneratedValue(strategy = GenerationType.UUID)
    @Column(name = "scrap_id", updatable = false, nullable = false)
    private UUID scrapId;

    @ManyToOne(fetch = FetchType.LAZY) // 지연 로딩 권장
    @JoinColumn(name = "user_id", nullable = false)
    private User user;

    @Column(nullable = false, length = 50)
    private String name;

    @Column(name = "thumbnail_url", length = 255) // ERD 상 NULL 허용(NULLABLE)
    private String thumbnailUrl;

    @Column(nullable = false, length = 20)
    private String color;
}
