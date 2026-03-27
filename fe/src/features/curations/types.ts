/** /api/curation/minimap 응답 - 카페 미니맵 단건 */
export interface CurationMinimapData {
  cafeId: string;
  name: string;
  latitude: number;
  longitude: number;
}

export interface CurationMinimapResponse {
  status: string;
  data: CurationMinimapData;
  message: string | null;
}

/** /api/curation/cafeList 응답 - 카테고리별 카페 리스트 */
export interface CurationCafeListItem {
  cafeId: string;
  thumbnailUrl: string;
  name: string;
  cafeIntro: string;
  roadAddress: string;
}

export interface CurationCafeListResponse {
  status: string;
  data: {
    cafeList: CurationCafeListItem[];
  };
  message: string | null;
}
