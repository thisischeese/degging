// 스크랩 카테고리 내 카페 아이템 (상세 조회용)
export interface ScrapCafeItem {
    cafeId: string; // UUID
    name: string;
    cafeIntro: string; // 명세서 명칭
    address?: string; // 상세 정보에 포함될 수 있음
    imageUrl?: string; // 상세 정보에 포함될 수 있음
}

// 별(스타) 아이콘 색상 타입 (백엔드 대문자 응답에 맞춤)
export type StarColor = 'RED' | 'PINK' | 'IVORY' | 'MINT' | 'GREEN' | 'SKY' | 'YELLOW' | 'PURPLE' | 'BROWN';

// 스크랩 카테고리 (폴더) 정보
export interface ScrapCategory {
    scrapId: string | null; // "모든 스크랩"은 null로 옴
    name: string;
    color: StarColor | null; // 명세서 명칭
    thumbnailUrl: string[]; // 리스트 조회 시 (명세서: thumbnailUrl)
}

// 스크랩 상세 정보
export interface ScrapDetail {
    scrapId: string;
    name: string;
    color: StarColor;
    cafes: ScrapCafeItem[];
    thumbnailUrls: string[]; // 상세 조회 시 (명세서: thumbnailUrls)
}
