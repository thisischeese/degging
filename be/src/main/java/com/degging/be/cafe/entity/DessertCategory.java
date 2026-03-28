package com.degging.be.cafe.entity;

/**
 * 온보딩 메뉴용 대표 디저트 정의 클래스
 */
import lombok.Getter;
import lombok.RequiredArgsConstructor;
import java.util.Arrays;
import java.util.List;

@Getter
@RequiredArgsConstructor
public enum DessertCategory {

    // 🔥 초강력 핫 트렌드
    DUBAI_CHOCOLATE("두바이 초콜릿", Arrays.asList("두바이 초콜릿", "두바이초콜릿", "카다이프 초콜릿")),
    DUBAI_COOKIE("두바이 쫀득쿠키", Arrays.asList("두바이 쫀득", "두바이 쿠키", "두바이쿠키")),
    CROOKIE("크루키", Arrays.asList("크루키")),
    YOGURT_ICE_CREAM("요거트 아이스크림", Arrays.asList("요거트 아이스크림", "요아정", "요거트아이스크림")),

    // 🧈 꾸덕 & 쫀득 시리즈
    BUTTER_BAR("버터바", Arrays.asList("버터바", "황치즈 버터바", "꾸덕바")),
    BUTTER_TTEOK("버터떡", Arrays.asList("버터떡")),
    HWANG_CHEESE("황치즈", Arrays.asList("황치즈", "뽀또")),
    BANANA_PUDDING("바나나 푸딩", Arrays.asList("바나나 푸딩", "바나나푸딩", "매그놀리아")),

    // 🥐 식사 대용 빵 & 페이스트리
    SALT_BREAD("소금빵", Arrays.asList("소금빵", "시오빵")),
    BAGEL("베이글", Arrays.asList("베이글", "베이글샌드위치")),
    CROFFLE("크로플", Arrays.asList("크로플", "크로와상 와플")),

    // ☕ 겉바속촉 구움과자
    FINANCIER("휘낭시에", Arrays.asList("휘낭시에", "피낭시에")),
    CANELE("까눌레", Arrays.asList("까눌레", "까늘레")),
    EGG_TART("에그타르트", Arrays.asList("에그타르트", "에그 타르트")),

    // 🇰🇷 K-디저트의 진화
    GAESEONG_JUAK("개성주악", Arrays.asList("개성주악", "주악")),
    YAKGWA_COOKIE("약과 쿠키", Arrays.asList("약과 쿠키", "약과쿠키", "약과")),

    // ❄️ 영원한 스테디셀러 & 콜드 디저트
    MACARON("마카롱", Arrays.asList("마카롱", "뚱카롱")),
    GREEK_YOGURT("그릭 요거트", Arrays.asList("그릭요거트", "그릭 요거트", "그릭")),
    GELATO("젤라또", Arrays.asList("젤라또", "젤라토")),
    BINGSU("빙수", Arrays.asList("빙수", "눈꽃빙수", "망고빙수")),

    // 예외 처리용 (위 20개에 안 걸리는 경우)
    OTHER("기타", Arrays.asList());

    private final String description; // 프론트에 노출될 이름 (예: "두바이 쫀득쿠키")
    private final List<String> matchKeywords; // 크롤링 데이터 매칭용

    /**
     * 크롤링된 메뉴명에 키워드가 포함되어 있으면 해당 카테고리로 자동 분류합니다.
     */
    public static DessertCategory matchCategory(String menuName) {
        if (menuName == null || menuName.trim().isEmpty()) {
            return OTHER;
        }

        // 띄어쓰기 없이 붙여서 검색 확률을 높임 (선택 사항)
        String normalizedMenuName = menuName.replace(" ", "");

        return Arrays.stream(DessertCategory.values())
                .filter(category -> category != OTHER)
                .filter(category -> category.getMatchKeywords().stream()
                        .map(keyword -> keyword.replace(" ", "")) // 키워드도 띄어쓰기 제거 후 비교
                        .anyMatch(normalizedMenuName::contains))
                .findFirst()
                .orElse(OTHER);
    }
}
