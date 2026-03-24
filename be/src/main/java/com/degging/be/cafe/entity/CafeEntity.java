package com.degging.be.cafe.entity;

import com.degging.be.cafe.dto.response.external.KakaoPlaceItem;
import com.degging.be.cafe.dto.response.external.StoreListInUpjongItem;
import com.degging.be.global.entity.BaseEntity;
import jakarta.persistence.*;
import lombok.*;
import org.locationtech.jts.geom.Point;

import java.util.ArrayList;
import java.util.List;
import java.util.UUID;

/**
 * 카페 정보를 저장하는 엔티티 클래스
 *
 * BaseEntity 상속으로 생성/수정 시간 자동 관리
 */
@Entity
@Getter
@Builder
@NoArgsConstructor(access = AccessLevel.PROTECTED)
@AllArgsConstructor
@Table(name = "cafes")
public class CafeEntity extends BaseEntity {

    @Id
    @GeneratedValue(strategy = GenerationType.UUID)
    @Column(updatable = false, nullable = false)
    private UUID cafeId;

    @Column(nullable = false, unique = true)
    private String bizesId; // 소상공인시장진흥공단 상가업소번호

    @Column(unique = true)
    private String kakaoPlaceId; // 카카오 장소 검색 API 식별자

    @Column(nullable = false)
    private String name; // 상호명

    private String brandName; // 정제된 브랜드명 (ex. 스타벅스)

    private String branchName; // 지점명 (ex. 역삼역점)

    private String address; // 주소

    private String roadAddress; // 도로명 주소

    private String phone; // 전화번호

    private String thumbnailUrl; // 썸네일 이미지 url

    @Enumerated(EnumType.STRING)
    @Column(nullable = false)
    private CafeStatus status; // Enum으로 지정된 영업 상태 (영업/폐업/상태확인불가)

    @Enumerated(EnumType.STRING)
    @Column(nullable = false)
    private CafeCategory category; // 카페 카테고리 (커피, 제과, 디저트)

    @Column(columnDefinition = "geography(Point,4326)", nullable = false)
    private Point location; // 카페 위치 PostGIS

    private String cafeIntro; // 카페 한줄 소개

    @OneToOne(mappedBy = "cafe", cascade = CascadeType.ALL)
    private CafeBusinessHoursEntity businessHoursEntity; // 요일별 영업시간 1:1 매핑

    @Column(nullable = false)
    @Builder.Default
    private boolean franchise = false; // 프랜차이즈 여부

    // 평점 통계 연관관계 추가
    @OneToOne(mappedBy = "cafe", cascade = CascadeType.ALL)
    private CafeRatingStatsEntity ratingStats;

    // 이미지 리스트 연관관계 추가
    @Builder.Default
    @OneToMany(mappedBy = "cafe", cascade = CascadeType.ALL, orphanRemoval = true, fetch = FetchType.LAZY)
    private List<CafeImageEntity> images = new ArrayList<>();

    // 메뉴 리스트 연관관계 추가
    @Builder.Default
    @OneToMany(mappedBy = "cafe", cascade = CascadeType.ALL, orphanRemoval = true, fetch = FetchType.LAZY)
    private List<CafeMenuEntity> menus = new ArrayList<>();

    // 분위기 태그 매핑 연관관계 추가
    @Builder.Default
    @OneToMany(mappedBy = "cafe", cascade = CascadeType.ALL, orphanRemoval = true, fetch = FetchType.LAZY)
    private List<CafeVibeTagEntity> vibeTags = new ArrayList<>();

    /**
     * 상가정보 API 응답 데이터를 기반으로 기본 카페 엔티티 생성
     *
     * @param item      상가정보 API에서 조회한 업소 데이터
     * @param kakaoItem 가져온 상가정보와 매칭된 카카오 API 데이터
     * @param location  카페 위치 정보 (PostGIS Point)
     * @param category  판별된 카페 카테고리 (커피, 제과, 디저트)
     * @return 생성된 CafeEntity 객체
     */
    public static CafeEntity of(StoreListInUpjongItem item, KakaoPlaceItem kakaoItem, Point location, CafeCategory category) {
        // 기존 소상공인 데이터명 대신 카카오 API 기반 업소 적용
        String originalName = kakaoItem != null && kakaoItem.getPlaceName() != null
                ? kakaoItem.getPlaceName()
                : item.getBizesNm();
        String branchName = toNullIfBlank(item.getBrchNm());

        // 상호명에서 지점명을 제거하여 브랜드명 추출
        String brandName = originalName;
        if (branchName != null) {
            brandName = originalName.replace(branchName, "").replaceAll("\\s+", " ").trim();
        }

        return CafeEntity.builder()
                .bizesId(item.getBizesId())
                .kakaoPlaceId(kakaoItem.getId())
                .name(originalName)
                .brandName(brandName)
                .branchName(branchName)
                .address(toNullIfBlank(item.getLnoAdr()))
                .roadAddress(toNullIfBlank(item.getRdnmAdr()))
                .phone(kakaoItem.getPhone())
                .thumbnailUrl(null)
                .status(CafeStatus.OPEN)
                .category(category)
                .location(location)
                .cafeIntro(null)
                .build();
    }

    /**
     * 문자열이 null이거나 공백이면 null로 변환
     *
     * @param value 변환할 문자열 값
     * @return value가 null 또는 공백이면 null, 그렇지 않으면 원래 문자열 반환
     */
    private static String toNullIfBlank(String value) {
        if (value == null || value.isBlank()) {
            return null;
        }
        return value;
    }

    /**
     * 인허가 데이터 기반 영업 상태 업데이트
     *
     * 서울시 인허가 정보 API를 통해 확인된 영업/폐업 상태를 엔티티에 반영
     */
    public void updateStatus(CafeStatus status) {
        this.status = status;
    }

    /**
     * 프렌차이즈 여부 업데이트
     * 
     * @param isFranchise 프렌차이즈 여부
     */
    public void updateFranchise(boolean isFranchise) {
        this.franchise = isFranchise;
    }

    /**
     * 크롤링된 부가 정보 업데이트
     */
    public void updateCrawledData(String thumbnailUrl, String cafeIntro) {
        this.thumbnailUrl = thumbnailUrl;
        this.cafeIntro = cafeIntro;
    }
}
