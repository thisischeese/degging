package com.degging.be.cafe.entity;

import com.degging.be.infra.external.dto.response.KakaoPlaceItem;
import com.degging.be.infra.external.dto.response.StoreListInUpjongItem;
import com.degging.be.global.entity.BaseEntity;
import jakarta.persistence.*;
import lombok.*;
import org.locationtech.jts.geom.Point;

import java.util.ArrayList;
import java.util.Arrays;
import java.util.List;
import java.util.UUID;
import com.degging.be.global.converter.VectorConverter;
import org.hibernate.annotations.ColumnTransformer;

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

    // 프랜차이즈 판별을 위한 브랜드명 목록 (인식률 향상을 위해 핵심 키워드 위주로 구성)
    private static final List<String> FRANCHISE_NAMES = Arrays.asList(
            "스타벅스", "이디야", "투썸플레이스", "메가MGC커피", "메가커피", "컴포즈커피", "컴포즈", "빽다방", "커피빈",
            "폴바셋", "할리스", "엔제리너스", "파스쿠찌", "탐앤탐스", "드롭탑", "매머드커피", "매머드", "바나프레소",
            "텐퍼센트", "커피에반하다", "공차", "더벤티", "쥬씨", "아마스빈", "달콤커피", "만랩커피", "커피나무",
            "카페인중독", "브루다커피", "에이바우트", "블루보틀", "테라로사", "팀홀튼", "와플대학",
            "배스킨라빈스", "베스킨라빈스", "던킨", "파리바게뜨", "파리바게트", "뚜레쥬르", "설빙", "커피빈", 
            "아티제", "커피스미스", "커피나인", "백억커피", "백억", "디저트39", "디저트 39");

    /**
     * 이름에 포함된 프랜차이즈 명칭을 반환
     */
    public static String getMatchedFranchiseName(String name) {
        if (name == null)
            return null;
        for (String fName : FRANCHISE_NAMES) {
            if (name.contains(fName)) {
                return fName;
            }
        }
        return null;
    }

    @Id
    @GeneratedValue(strategy = GenerationType.UUID)
    @Column(updatable = false, nullable = false)
    private UUID cafeId;

    @Column(unique = true)
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

    @Column
    private String thumbnailUrl; // 썸네일 이미지 url

    @Enumerated(EnumType.STRING)
    @Column(nullable = false)
    private CafeStatus status; // Enum으로 지정된 영업 상태 (영업/폐업/상태확인불가)

    @Enumerated(EnumType.STRING)
    @Column(nullable = false)
    private CafeCategory category; // 카페 카테고리 (커피, 제과, 디저트)

    @Column(columnDefinition = "geography(Point,4326)", nullable = false)
    private Point location; // 카페 위치 PostGIS

    @Convert(converter = VectorConverter.class)
    @Column(columnDefinition = "vector(64)")
    @ColumnTransformer(write = "?::vector")
    private float[] cafeVector; // 카페 대표 벡터

    @Column(length = 500)
    private String cafeIntro; // 카페 한줄 소개

    @OneToOne(mappedBy = "cafe", cascade = CascadeType.ALL)
    private CafeBusinessHoursEntity businessHoursEntity; // 요일별 영업시간 1:1 매핑

    @Column(nullable = false)
    @Builder.Default
    private boolean franchise = false; // 프랜차이즈 여부

    @Column(nullable = false)
    @Builder.Default
    private boolean isCafe = true; // 실제 카페 여부 (부적절한 데이터 필터링용)

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
    public static CafeEntity of(StoreListInUpjongItem item, KakaoPlaceItem kakaoItem, Point location,
            CafeCategory category) {
        // 기존 소상공인 데이터명 대신 카카오 API 기반 업소 적용
        String originalName = kakaoItem != null && kakaoItem.getPlaceName() != null
                ? kakaoItem.getPlaceName()
                : item.getBizesNm();
        String branchName = toNullIfBlank(item.getBrchNm());

        // 상호명에서 지점명을 제거하여 브랜드명 추출
        String brandName = originalName;
        boolean isFranchise = false;

        // 프랜차이즈 목록에 포함되어 있는지 확인
        for (String fName : FRANCHISE_NAMES) {
            if (originalName.contains(fName)) {
                brandName = fName;
                isFranchise = true;

                // 지점명이 비어있는 경우, 상호명에서 브랜드명을 제외한 나머지를 지점명으로 추출 시도
                if (branchName == null && !originalName.equals(fName)) {
                    String extractedBranch = originalName.replace(fName, "").replaceAll("\\s+", " ").trim();
                    if (!extractedBranch.isEmpty()) {
                        branchName = extractedBranch;
                    }
                }
                break;
            }
        }

        // 지점명이 존재하면 지점명 제거 시도
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
                .franchise(isFranchise)
                .isCafe(true)
                .build();
    }

    /**
     * 카카오 API 응답 데이터를 기반으로 직접 카페 엔티티 생성 (공공데이터에 없는 경우 대비)
     */
    public static CafeEntity of(KakaoPlaceItem kakaoItem, Point location, CafeCategory category) {
        String originalName = kakaoItem.getPlaceName();
        String brandName = originalName;
        String branchName = null;
        boolean isFranchise = false;

        // 프랜차이즈 목록에 포함되어 있는지 확인
        for (String fName : FRANCHISE_NAMES) {
            if (originalName.contains(fName)) {
                brandName = fName;
                isFranchise = true;

                if (!originalName.equals(fName)) {
                    String extractedBranch = originalName.replace(fName, "").replaceAll("\\s+", " ").trim();
                    if (!extractedBranch.isEmpty()) {
                        branchName = extractedBranch;
                    }
                }
                break;
            }
        }

        return CafeEntity.builder()
                .bizesId(null) // 공공데이터 ID 없음
                .kakaoPlaceId(kakaoItem.getId())
                .name(originalName)
                .brandName(brandName)
                .branchName(branchName)
                .address(toNullIfBlank(kakaoItem.getAddressName()))
                .roadAddress(toNullIfBlank(kakaoItem.getRoadAddressName()))
                .phone(kakaoItem.getPhone())
                .status(CafeStatus.OPEN)
                .category(category)
                .location(location)
                .franchise(isFranchise)
                .isCafe(true)
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
     * 프렌차이즈 정보 일괄 업데이트
     * 
     * @param brandName   정제된 브랜드명
     * @param branchName  지점명
     * @param isFranchise 프렌차이즈 여부
     */
    public void updateFranchiseInfo(String brandName, String branchName, boolean isFranchise) {
        this.brandName = brandName;
        this.branchName = branchName;
        this.franchise = isFranchise;
    }

    /**
     * 크롤링된 부가 정보 업데이트
     */
    public void updateCrawledData(String thumbnailUrl, String cafeIntro) {
        this.thumbnailUrl = thumbnailUrl;
        this.cafeIntro = cafeIntro;
    }

    /**
     * 실제 카페로 판별된 경우 상태 변경 (복구용)
     */
    public void markAsCafe() {
        this.isCafe = true;
    }

    /**
     * 비카페성 시설로 판별된 경우 상태 변경 (필터링용)
     */
    public void markAsNonCafe() {
        this.isCafe = false;
    }

    public void setBusinessHoursEntity(CafeBusinessHoursEntity businessHoursEntity) {
        this.businessHoursEntity = businessHoursEntity;
    }

    public void setRatingStats(CafeRatingStatsEntity ratingStats) {
        this.ratingStats = ratingStats;
    }
}
