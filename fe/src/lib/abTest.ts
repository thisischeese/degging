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
 * 백엔드에서 받은 A/B 그룹 정보를 프론트엔드 저장소와 동기화합니다.
 * 값이 다를 경우에만 GTM으로 이벤트를 다시 전송하여 정확도를 높입니다.
 * @param group 'A' | 'B'
 */
export const setAbGroup = (group: 'A' | 'B') => {
  if (typeof window === 'undefined') return;

  const STORAGE_KEY = 'degging_ab_group';
  const currentGroup = localStorage.getItem(STORAGE_KEY);

  if (currentGroup !== group) {
    localStorage.setItem(STORAGE_KEY, group);
    // 그룹이 변경되었을 때만 새롭게 이벤트 전송
    pushGtmEvent('ab_group_assigned', { group });
  }
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
