export interface DiscoveryFeedItem {
    cafeId: string;
    image: string; // UUID
    thumbnailUrl?: string; // fallback
}

export interface DiscoverySliceResponse {
    content: DiscoveryFeedItem[];
    pageable: {
        pageNumber: number;
        pageSize: number;
    };
    number: number;
    size: number;
    numberOfElements: number;
    first: boolean;
    last: boolean;
    empty: boolean;
}
