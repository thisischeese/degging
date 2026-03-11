/** 실시간 디저트 랭킹 아이템 타입 */
export interface RankingItem {
  rank: number;    // 순위
  keyword: string; // 검색어 (디저트 이름)
}

/** 랭킹 API 응답 타입 */
export interface RankingResponse {
  rankings: RankingItem[];
  // 나중에 필요하다면 업데이트 시간 등을 추가할 수 있습니다.
  // updatedAt?: string; 
}