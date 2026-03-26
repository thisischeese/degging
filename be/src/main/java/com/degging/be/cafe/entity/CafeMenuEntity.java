package com.degging.be.cafe.entity;

import jakarta.persistence.*;
import lombok.*;

@Entity
@Table(name = "cafe_menus")
@Getter
@Builder
@NoArgsConstructor(access = AccessLevel.PROTECTED)
@AllArgsConstructor
public class CafeMenuEntity {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long menuId;    // 개별 메뉴 ID

    @Column(nullable = false, length = 100)
    private String menuName;    // 메뉴명

    private Integer price;  // 금액

    @Column(length = 500)
    private String menuDescription; // 메뉴 설명

    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "cafe_id", nullable = false)
    private CafeEntity cafe;    // 카페
}