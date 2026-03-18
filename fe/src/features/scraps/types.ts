// 스크랩 카테고리에 포함된 카페 썸네일 정보
export interface ScrapThumbnail {
    cafeId: number;
    imageUrl: string;
}

// 별(스타) 아이콘 색상 타입
export type StarColor = 'red' | 'pink' | 'ivory' | 'mint' | 'green' | 'sky';

// 스크랩 카테고리 (폴더) 정보
export interface ScrapCategory {
    categoryId: number;
    name: string;
    starColor: StarColor;
    thumbnails: ScrapThumbnail[];
}
