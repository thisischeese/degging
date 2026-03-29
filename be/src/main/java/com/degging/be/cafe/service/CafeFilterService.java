package com.degging.be.cafe.service;

import com.degging.be.cafe.client.KakaoLocalApiClient;
import com.degging.be.cafe.dto.response.external.KakaoPlaceItem;
import com.degging.be.cafe.dto.response.external.KakaoPlaceResponse;
import com.degging.be.cafe.dto.response.external.StoreListInUpjongItem;
import com.degging.be.cafe.entity.CafeCategory;
import com.degging.be.cafe.entity.CafeEntity;
import com.degging.be.cafe.repository.CafeRepository;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.util.List;

/**
 * 상가업소 데이터에서 실제 카페만 선별하기 위한 필터 서비스
 *
 * 필터 순서
 * 1. 상호명 기반 제외 키워드 필터
 * 2. 상권 업종 소분류명이 카페인지 확인
 * 3. 표준산업분류명이 커피/비알코올 계열인지 확인
 */
@Slf4j
@Service
@RequiredArgsConstructor
public class CafeFilterService {

    private final CafeRepository cafeRepository;
    private final KakaoLocalApiClient kakaoLocalApiClient;

    // 제외할 키워드 목록
    private static final List<String> EXCLUDE_KEYWORDS = List.of(
            // 만화/게임/전진 계열
            "만화카페", "놀숲", "벌툰", "툰카페", "만화", "북카페", "보드게임", "보드카페", 
            "방탈출", "이스케이프", "pc카페", "pc방", "pczone", "피시방", "vr카페", "vr게임", "게임카페", "인터넷카페",

            // 동물/키즈 계열
            "고양이카페", "애견카페", "강아지카페", "펫카페", "키즈카페", "키즈룸",

            // 룸/멀티/스터디 계열
            "룸카페", "카페룸", "룸", "멀티카페", "멀티플레이스", "멀티", "스터디카페", "스터디룸", "독서실",

            // 일반 음식점/술집 계열 (카페와 혼동될 수 있는 것 포함)
            "식당", "음식점", "레스토랑", "초밥", "스시", "일식", "한식", "중식", "양식", "불고기", "갈비", "삼겹살",
            "치킨", "돈까스", "정식", "부대찌개", "냉면", "마라탕", "쌀국수", "피자", "파스타", "족발", "보쌈", "포차", 
            "이자카야", "호프", "술집", "주점", "포장마차", "맥주", "와인바", "바(bar)",

            // 금융/의료/기관/공공 계열
            "은행", "금융", "보험", "증권", "투자", "신협", "새마을", "저축", "센터", "협회", "공사", "공단",
            "병원", "의원", "치과", "내과", "외과", "보건소", "약국", "치유센터", "힐링센터", "복지관", "문화센터", 
            "상담소", "체험관", "수련관", "전시관", "박물관", "미술관", "도서관", "문화원", "연구소", 

            // 교육/종교 계열
            "학교", "초등학교", "중학교", "고등학교", "대학교", "캠퍼스", "학원", "유치원", "어린이집", "교회", "성당", "사찰", "종교",

            // 숙박/기타 비카페성 시설
            "호텔", "모텔", "펜션", "게스트하우스", "주유소", "충전소", "정비소", "세탁소", "편의점", "마트", "슈퍼", 
            "백화점", "아울렛", "휴게실", "매점", "다방", "기원", "부동산", "인쇄", "문구", "안경", "다이소", "올리브영", 
            "롭스", "랄라블라", "문구점", "서점", "꽃집", "플라워", "클리닉", "피부관리", "헤어", "미용실", "바버샵"
    );

    /**
     * 해당 업소가 실제 카페인지 판단
     *
     * @param item 상가업소 데이터
     * @return 실제 카페이면 true, 아니면 false
     */
    public boolean isCafe(StoreListInUpjongItem item) {

        if (item == null) {
            return false;
        }

        String name = item.getBizesNm();
        String smallCategoryName = item.getIndsSclsNm();
        String ksicName = item.getKsicNm();

        if (name == null || name.isBlank()) {
            return false;
        }

        // 상호명 소문자 변환
        String normalizedName = name.toLowerCase();

        // 제외 키워드가 포함되면 카페가 아님
        for (String keyword : EXCLUDE_KEYWORDS) {
            if (normalizedName.contains(keyword.toLowerCase())) {
                return false;
            }
        }

        // 상권 업종 소분류명이 카페/디저트/제과 계열인지 확인
        boolean isValidCategory = smallCategoryName != null && (smallCategoryName.contains("카페") ||
                smallCategoryName.contains("제과") ||
                smallCategoryName.contains("빵") ||
                smallCategoryName.contains("베이커리") ||
                smallCategoryName.contains("디저트") ||
                smallCategoryName.contains("아이스크림") ||
                smallCategoryName.contains("빙수") ||
                smallCategoryName.contains("도넛") ||
                smallCategoryName.contains("샌드위치") ||
                smallCategoryName.contains("토스트"));

        if (!isValidCategory) {
            return false;
        }

        // 표준산업분류명이 커피/제과 계열인지 확인
        if (ksicName != null && (ksicName.contains("커피") || ksicName.contains("제과") || ksicName.contains("빵"))) {
            return true;
        }

        return false;
    }

    /**
     * 업종 정보를 기반으로 카페 카테고리 판별
     *
     * @param item 상가업소 데이터
     * @return 판별된 CafeCategory (기본값: COFFEE)
     */
    public CafeCategory determineCategory(StoreListInUpjongItem item) {
        String smallCategoryName = item.getIndsSclsNm();
        String ksicName = item.getKsicNm();

        if (smallCategoryName == null) {
            return CafeCategory.COFFEE;
        }

        // 1. 제과/베이커리 판별
        if (smallCategoryName.contains("제과") || smallCategoryName.contains("빵") ||
                smallCategoryName.contains("베이커리") || (ksicName != null && ksicName.contains("제과"))) {
            return CafeCategory.BAKERY;
        }

        // 2. 디저트/기타 판별
        if (smallCategoryName.contains("디저트") || smallCategoryName.contains("아이스크림") ||
                smallCategoryName.contains("빙수") || smallCategoryName.contains("도넛") ||
                smallCategoryName.contains("샌드위치") || smallCategoryName.contains("토스트")) {
            return CafeCategory.DESSERT;
        }

        // 3. 기본 및 카페 판별
        return CafeCategory.COFFEE;
    }

    /**
     * 카카오 API 데이터를 기반으로 카페 카테고리 판별
     *
     * @param item 카카오 장소 데이터
     * @return 판별된 CafeCategory (기본값: COFFEE)
     */
    public CafeCategory determineCategory(KakaoPlaceItem item) {
        String categoryName = item.getCategoryName();

        if (categoryName == null) {
            return CafeCategory.COFFEE;
        }

        // 1. 제과/베이커리 판별
        if (categoryName.contains("제과") || categoryName.contains("빵") ||
                categoryName.contains("베이커리")) {
            return CafeCategory.BAKERY;
        }

        // 2. 디저트/기타 판별
        if (categoryName.contains("디저트") || categoryName.contains("아이스크림") ||
                categoryName.contains("빙수") || categoryName.contains("도넛") ||
                categoryName.contains("샌드위치") || categoryName.contains("토스트")) {
            return CafeCategory.DESSERT;
        }

        // 3. 기본 및 카페 판별
        return CafeCategory.COFFEE;
    }

    /**
     * 기존 DB에 저장된 데이터 중 제외 키워드가 포함된 비카페 시설 식별 (isCafe = false)
     *
     * @return 식별된 비카페 시설 수
     */
    @Transactional
    public int identifyNonCafes() {
        log.info("기존 데이터 중 비카페성 시설 식별 및 표시 시작");
        List<CafeEntity> allCafes = cafeRepository.findAll();

        List<CafeEntity> identified = allCafes.stream()
                .filter(cafe -> {
                    String name = cafe.getName().toLowerCase();
                    return EXCLUDE_KEYWORDS.stream()
                            .anyMatch(keyword -> name.contains(keyword.toLowerCase()));
                })
                .peek(CafeEntity::markAsNonCafe)
                .toList();

        if (!identified.isEmpty()) {
            log.info("비카페성 시설 식별 완료 - 식별 건수: {}건 (isCafe=false 처리됨)", identified.size());
        } else {
            log.info("식별된 비카페성 시설이 없습니다.");
        }

        return identified.size();
    }

    /**
     * 카카오 API를 다시 호출하여 카테고리 정보 기반으로 비카페 시설 재검증 (메소드 B)
     * 안전을 위해 삭제하지 않고 isCafe = false 처리만 수행함
     *
     * @param limit 최대 처리 건수 (API 할당량 고려)
     * @return 식별된 비카페 시설 수
     */
    @Transactional
    public int revalidateWithKakao(int limit) {
        log.info("카카오 API 카테고리 기반 기존 데이터 재검증 시작 (제한: {}건)", limit);
        List<CafeEntity> cafes = cafeRepository.findAll().stream()
                .filter(CafeEntity::isCafe)
                .limit(limit)
                .toList();

        int identifiedCount = 0;
        for (CafeEntity cafe : cafes) {
            try {
                // 좌표 기반으로 해당 장소 재검색
                KakaoPlaceResponse response = kakaoLocalApiClient.searchPlaces(
                        cafe.getName(),
                        cafe.getLocation().getX(),
                        cafe.getLocation().getY(),
                        100, // 100m 이내 정밀 검색
                        1, 10
                );

                if (response != null && response.getDocuments() != null) {
                    boolean isValid = false;
                    for (KakaoPlaceItem item : response.getDocuments()) {
                        // ID가 일치하는 항목을 찾아서 카테고리 확인
                        if (item.getId().equals(cafe.getKakaoPlaceId())) {
                            if (isCafeCategory(item)) {
                                isValid = true;
                            }
                            break;
                        }
                    }

                    if (!isValid) {
                        cafe.markAsNonCafe();
                        identifiedCount++;
                        log.info("비카페 식별(카카오): {} (현재 카테고리: {})", cafe.getName(), 
                                 response.getDocuments().stream().filter(i -> i.getId().equals(cafe.getKakaoPlaceId()))
                                         .findFirst().map(KakaoPlaceItem::getCategoryName).orElse("N/A"));
                    }
                }
            } catch (Exception e) {
                log.error("카페 재검증 중 오류 발생: {}, 사유: {}", cafe.getName(), e.getMessage());
            }
        }

        log.info("카카오 재검증 완료 - 식별 건수: {}건", identifiedCount);
        return identifiedCount;
    }

    /**
     * 카카오 카테고리가 카페 계열인지 확인 (CafeDuplicateService의 로직 공유)
     */
    private boolean isCafeCategory(KakaoPlaceItem document) {
        String category = document.getCategoryName();
        String groupCode = document.getCategoryGroupCode();

        if ("CE7".equals(groupCode)) return true;
        
        if (category != null) {
            boolean isCafePath = category.contains("카페") || category.contains("커피") || 
                                 category.contains("제과") || category.contains("베이커리") || 
                                 category.contains("디저트") || category.contains("아이스크림") || 
                                 category.contains("도넛");

            boolean isExcludedPath = category.contains("술집") || category.contains("호프") || 
                                     category.contains("포차") || category.contains("이자카야") || 
                                     category.contains("주점");

            return isCafePath && !isExcludedPath;
        }
        return false;
    }
}