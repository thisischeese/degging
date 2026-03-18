/** 실시간 디저트 랭킹 아이템 타입 */
export interface RankingItem {
  rank: number;    // 순위
  keyword: string; // 검색어 (디저트 이름)
}

/** 랭킹 API 응답 타입 */
export interface RankingResponse {
  status: string;    // "success"
  code: string;      // "200"
  message: string;   // 응답 메시지
  data: {
    rankings: RankingItem[];
  };
}