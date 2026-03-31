package com.degging.be.scrap.entity;

import com.degging.be.global.entity.BaseEntity;
import com.degging.be.user.entity.UserEntity;
import jakarta.persistence.Entity;
import jakarta.persistence.Id;
import jakarta.persistence.ManyToOne;

import java.util.ArrayList;
import java.util.List;
import java.util.UUID;
import jakarta.persistence.*;
import lombok.*;
import org.hibernate.annotations.JdbcTypeCode;
import org.hibernate.type.SqlTypes;

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
    private UserEntity user;

    @Column(nullable = false, length = 50)
    private String name;

    @Builder.Default // builder 써도 기본값 설정 가능
    @JdbcTypeCode(SqlTypes.JSON)
    @Column(name = "thumbnail_urls", columnDefinition = "jsonb") // 최대 4장 JSONB 로 저장
    private List<String> thumbnailUrls = new ArrayList<>();

    @Column(nullable = false, length = 20)
    private String color;

    // 기본폴더 여부
    @Column(nullable = false)
    @Builder.Default
    private boolean isDefault = false;
    
    // 스크랩에 포함된 항목(카페) 리스트
    @Builder.Default
    @OneToMany(mappedBy = "scrap", cascade = CascadeType.ALL, orphanRemoval = true)
    private List<ScrapItemEntity> scrapItems = new ArrayList<>();

    @Builder.Default
    @OneToMany(mappedBy = "scrap", cascade = CascadeType.ALL, orphanRemoval = true)
    private List<ScrapShareLinkEntity> shareLinks = new ArrayList<>();

    public void addShareLink(ScrapShareLinkEntity link) {
        this.shareLinks.add(link);
    }

    // 아이템 추가 시 사용
    public void addScrapItem(ScrapItemEntity item) {
        this.scrapItems.add(item);
        item.setScrap(this);
    }

    // 썸네일 업데이트용 메서드 (카페 추가/삭제 시 반영)
    public void updateThumbnailUrls(List<String> urls) {
        this.thumbnailUrls = urls;
    }

    // 스크랩 정보 업데이트
    public void update(String name, String color) {
        if (name != null && !name.isBlank()) {
            this.name = name;
        }
        if (color != null && !color.isBlank()){
            this.color = color;
        }
    }
}
