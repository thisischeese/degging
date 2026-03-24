package com.degging.be.cafe.service;

import com.degging.be.cafe.dto.response.external.StoreListInUpjongItem;
import com.degging.be.cafe.entity.CafeCategory;
import org.springframework.stereotype.Service;

import java.util.List;

/**
 * 상가업소 데이터에서 실제 카페만 선별하기 위한 필터 서비스
 *
 * 필터 순서
 * 1. 상호명 기반 제외 키워드 필터
 * 2. 상권 업종 소분류명이 카페인지 확인
 * 3. 표준산업분류명이 커피/비알코올 계열인지 확인
 */
@Service
public class CafeFilterService {

    // 제외할 키워드 목록
    private static final List<String> EXCLUDE_KEYWORDS = List.of(

            // 만화카페 계열
            "만화카페", "놀숲", "벌툰", "툰카페", "만화", "북카페",

            // 보드게임 계열
            "보드게임", "보드카페",

            // 방탈출 계열
            "방탈출", "이스케이프",

            // PC방 계열
            "pc카페", "pc방", "pczone", "피시방",

            // 스터디 계열
            "스터디카페", "스터디룸", "독서실",

            // 동물 카페 계열
            "고양이카페", "애견카페", "강아지카페", "펫카페",

            // 키즈카페 계열
            "키즈카페", "키즈룸",

            // 룸카페 계열
            "룸카페", "카페룸", "룸",

            // 멀티카페 계열
            "멀티카페", "멀티플레이스", "멀티",

            // vr/게임 계열
            "vr카페", "vr게임", "게임카페", "인터넷카페", "VR", "게임",

            // 기타 비카페성 시설
            "휴게실", "매점", "다방", "기원", "편의점", "마트", "슈퍼마켓", "백화점", "아울렛"
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
        boolean isValidCategory = smallCategoryName != null && (
                smallCategoryName.contains("카페") ||
                smallCategoryName.contains("제과") ||
                smallCategoryName.contains("빵") ||
                smallCategoryName.contains("베이커리") ||
                smallCategoryName.contains("디저트") ||
                smallCategoryName.contains("아이스크림") ||
                smallCategoryName.contains("빙수") ||
                smallCategoryName.contains("도넛") ||
                smallCategoryName.contains("샌드위치") ||
                smallCategoryName.contains("토스트")
        );
 
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
}