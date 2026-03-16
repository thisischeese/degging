package com.degging.be.scrap.entity;

import com.degging.be.global.entity.BaseEntity;
import jakarta.persistence.*;
import lombok.*;

/**
 * 스크랩 링크 공유에 사용하는 Entity
 */
@Entity
@Table(name = "scrap_share_links")
@Getter
@Builder
@NoArgsConstructor(access = AccessLevel.PROTECTED)
@AllArgsConstructor
public class ScrapShareLinkEntity extends BaseEntity {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    @Column(name = "link_id", updatable = false, nullable = false)
    private Long linkId;

    @Column(nullable = false, unique = true)
    private String token;

    @Builder.Default
    @Column(name = "is_active", nullable = false)
    private boolean isActive = true;

    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "scrap_id", nullable = false)
    private ScrapEntity scrap;

    // 링크 비활성화용 메서드
    public void deactivate() {
        this.isActive = false;
    }
}