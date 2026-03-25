declare global {
  interface Window {
    dataLayer: Record<string, unknown>[];
  }
}

/**
 * A/B 테스트 로컬 그룹을 확인합니다.
 * 배정된 그룹이 없으면 프론트엔드에서 무작위 배정하지 않고 null을 반환하여 백엔드 응답을 기다립니다.
 * @returns 'A' | 'B' | null
 */
export const getAbGroup = (): 'A' | 'B' | null => {
  if (typeof window === 'undefined') return 'A'; // SSR 환경 안전장치

  const STORAGE_KEY = 'degging_ab_group';
  const storedGroup = localStorage.getItem(STORAGE_KEY) as 'A' | 'B';

  if (storedGroup === 'A' || storedGroup === 'B') {
    return storedGroup;
  }

  // 이제 프론트엔드에서 무작위 배정을 하지 않습니다.
  // 백엔드 DB 값이 최우선이며, 로컬에 저장된 값이 없다면 null을 반환하여 백엔드 응답을 기다립니다.
  return null;
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
    pushGtmEvent('ab_group_assigned', { ab_group: group });
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
