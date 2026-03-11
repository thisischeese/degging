package com.degging.be.cafe.service;

import com.degging.be.cafe.dto.response.StoreListInUpjongItem;
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
            "만화카페", "놀숲", "벌툰", "툰카페", "만화",

            // 보드게임 계열
            "보드게임", "보드카페",

            // 방탈출 계열
            "방탈출",

            // PC방 계열
            "pc카페", "pc방", "pczone", "피시방",

            // 스터디 계열
            "스터디카페", "스터디룸", "독서실",

            // 동물 카페 계열
            "고양이카페", "애견카페", "강아지카페", "펫카페",

            // 키즈카페 계열
            "키즈카페", "키즈룸",

            // 룸카페 계열
            "룸카페", "카페룸",

            // 멀티카페 계열
            "멀티카페", "멀티플레이스",

            // vr/게임 계열
            "vr카페", "vr게임", "게임카페", "인터넷카페",

            // 기타 비카페성 시설
            "휴게실", "매점"
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

        // 상권 업종 소분류가 카페가 아니면 저장하지 않음
        if (smallCategoryName == null || !smallCategoryName.contains("카페")) {
            return false;
        }

        // 표준산업분류명이 "커피"를 포함하면 카페로 판단 (ex. 커피 전문점)
        if (ksicName != null && ksicName.contains("커피")) {
            return true;
        }

        return false;
    }
}