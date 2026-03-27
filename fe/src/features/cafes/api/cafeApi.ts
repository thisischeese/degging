import { axios_instance } from "@/api/axios_instance";
import { CafeDetailResponse, SearchCafesRequest, SearchCafesResponse, SearchCafeItem, Menu } from "../types";

// [실제 API 연동] cafeId를 받아 카페의 상세 정보를 조회합니다.
export const getCafeDetail = async (cafeId: string): Promise<CafeDetailResponse['data']> => {
  const response = (await axios_instance.get<CafeDetailResponse>(`/api/cafes/${cafeId}`)) as unknown as CafeDetailResponse;
  
  const data = response.data;
  const baseUrl = process.env.NEXT_PUBLIC_CLOUDFRONT_URL || '';

  // 카페 이미지 배열에 baseURL 추가
  if (data && Array.isArray(data.images) && data.images.length > 0) {
    data.images = data.images.map((img) => {
      if (img && !img.startsWith('http') && !img.startsWith('/')) {
        return `${baseUrl}/${img}`;
      }
      return img;
    });
  }

  // 메뉴 이미지에 baseURL 추가 (응답의 menuImageUrl 처리)
  if (data && Array.isArray(data.menus) && data.menus.length > 0) {
    data.menus = data.menus.map((menu: Menu) => {
      const targetImage = menu.menuImageUrl || menu.image;
      if (targetImage && !targetImage.startsWith('http') && !targetImage.startsWith('/')) {
        const fullUrl = `${baseUrl}/${targetImage}`;
        menu.menuImageUrl = fullUrl;
        menu.image = fullUrl; // UI 호환성을 위해 image 필드에도 할당
      }
      return menu;
    });
  }

  return data;
};

// [실제 API 연동] 키워드, 내 위치, 그리고 조건(Mood)에 따라 카페를 검색합니다.
export const searchCafes = async (payload: SearchCafesRequest): Promise<SearchCafeItem[]> => {
  /* 기존 코드 보존: 복합 조건(mood)이 있을 경우 POST, 단순 키워드 검색일 경우 GET 사용
  if (payload.mood && payload.mood.length > 0) {
    const response = await axios_instance.post<SearchCafesResponse>(`/api/cafes/search`, payload) as unknown as SearchCafesResponse;
    // 응답이 data 배열 형태일 수도 있고, data.cafes 일 수도 있으므로 방어적 접근
    return Array.isArray(response.data) ? response.data : (response.data?.cafes || []);
  } else {
    const response = await axios_instance.get<SearchCafesResponse>(`/api/cafes/search`, {
      params: {
        keyword: payload.keyword,
        latitude: payload.latitude,
        longitude: payload.longitude,
      }
    }) as unknown as SearchCafesResponse;
    return Array.isArray(response.data) ? response.data : (response.data?.cafes || []);
  }
  */

  // [수정] 통합된 POST API 명세 활용
  const requestBody = {
    mood: payload.mood || [],
    keyword: payload.keyword || '',
    latitude: payload.latitude,
    longitude: payload.longitude,
  };

  const response = await axios_instance.post<SearchCafesResponse>(`/api/cafes/search`, requestBody) as unknown as SearchCafesResponse;
  
  // 성공적으로 data 안에 cafes 가 내려온다고 가정 (명세 참고: data.cafes 배열)
  const resultData = response.data as unknown as { cafes?: SearchCafeItem[] };
  
  return Array.isArray(resultData) ? resultData : (resultData?.cafes || []);
};
