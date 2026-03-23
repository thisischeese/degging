// 스크랩 카테고리 내 카페 아이템 (상세 조회용)
export interface ScrapCafeItem {
    cafeId: string; // UUID
    name: string;
    cafeIntro: string;
    address?: string;
    thumbnailUrl?: string;
}

// 별(스타) 아이콘 색상 타입 (백엔드 대문자 응답에 맞춤)
export type StarColor = 'RED' | 'PINK' | 'IVORY' | 'MINT' | 'GREEN' | 'SKY' | 'YELLOW' | 'PURPLE' | 'BROWN';

// 스크랩 상세 조회
export interface ScrapDetail {
    scrapId: string | null; // "모든 스크랩"은 null로 옴 
    name: string;
    cafes: ScrapCafeItem[];
}

// 스크랩 목록 정보
export interface ScrapList {
    scrapId: string | null; // "모든 스크랩"은 null로 옴 
    name: string;
    color: StarColor | null;
    thumbnailUrl: string[]; //  최대 4개까지 back end에서 보내줌
}
