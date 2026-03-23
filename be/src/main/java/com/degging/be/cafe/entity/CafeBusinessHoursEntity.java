package com.degging.be.cafe.entity;

import jakarta.persistence.*;
import lombok.*;

import java.util.UUID;

/**
 * 카페 요일별 영업시간 엔티티 클래스
 */
@Entity
@Getter
@Builder
@NoArgsConstructor(access = AccessLevel.PROTECTED)
@AllArgsConstructor
@Table(name = "cafe_business_hours")
public class CafeBusinessHoursEntity {

    @Id
    @Column(name = "cafe_id")
    private UUID cafeId;

    @OneToOne
    @MapsId
    @JoinColumn(name = "cafe_id")
    private CafeEntity cafe;

    @Column(name = "mon_hours")
    private String monHours;

    @Column(name = "tues_hours")
    private String tuesHours;

    @Column(name = "wed_hours")
    private String wedHours;

    @Column(name = "thur_hours")
    private String thurHours;

    @Column(name = "fri_hours")
    private String friHours;

    @Column(name = "sat_hours")
    private String satHours;

    @Column(name = "sun_hours")
    private String sunHours;

    public void updateCrawledHours(String mon, String tue, String wed, String thu, String fri, String sat, String sun) {
        this.monHours = mon;
        this.tuesHours = tue;
        this.wedHours = wed;
        this.thurHours = thu;
        this.friHours = fri;
        this.satHours = sat;
        this.sunHours = sun;
    }

}
