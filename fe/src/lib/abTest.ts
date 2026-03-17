declare global {
  interface Window {
    dataLayer: Record<string, unknown>[];
  }
}

/**
 * A/B 테스트 로컬 그룹을 확인하고 배정합니다. (1주일 단기 테스트용)
 * 최초 배정 시 랜덤(50:50)으로 'A' 또는 'B'를 설정하고 GTM으로 전송합니다.
 * @returns 'A' | 'B'
 */
export const getAbGroup = (): 'A' | 'B' => {
  if (typeof window === 'undefined') return 'A'; // SSR 환경 안전장치

  const STORAGE_KEY = 'degging_ab_group';
  const storedGroup = localStorage.getItem(STORAGE_KEY) as 'A' | 'B';

  if (storedGroup === 'A' || storedGroup === 'B') {
    return storedGroup;
  }

  // 그룹이 없으면 랜덤(50:50) 배정
  const newGroup = Math.random() < 0.5 ? 'A' : 'B';
  localStorage.setItem(STORAGE_KEY, newGroup);
  
  // 최초 배정 시 GTM으로 이벤트 전송
  pushGtmEvent('ab_group_assigned', { group: newGroup });

  return newGroup;
};

/**
 * Google Tag Manager의 dataLayer에 이벤트를 안전하게 전송합니다.
 * @param eventName 전송할 이벤트 이름 (예: 'search_keyword', 'cafe_scrapped')
 * @param params 이벤트와 함께 보낼 추가 데이터
 */
export const pushGtmEvent = (eventName: string, params?: Record<string, unknown>) => {
  if (typeof window !== 'undefined') {
    window.dataLayer = window.dataLayer || [];
    window.dataLayer.push({
      event: eventName,
      ...params,
    });
  }
};
