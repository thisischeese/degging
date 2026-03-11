package com.degging.be.scrap.entity;

import com.degging.be.cafe.entity.CafeEntity;
import com.degging.be.global.entity.BaseEntity;
import jakarta.persistence.*;
import lombok.*;

import java.util.UUID;

/**
 * Scrap - Cafe 연관 관계를 나타내는 ScrapItems 정보를 나타내는 Entity
 */
@Entity
@Table(name = "scrap_items")
@Getter
@Builder
@NoArgsConstructor(access = AccessLevel.PROTECTED)
@AllArgsConstructor
public class ScrapItemEntity extends BaseEntity {
    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long scrapItemId;

    @Setter // 아이템 추가 시 사용
    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "scrap_id")
    private ScrapEntity scrap;

    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "cafe_id")
    private CafeEntity cafe; // 카페 정보

}
