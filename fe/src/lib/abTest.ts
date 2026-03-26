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
 * @param group 'A' | 'B'
 */
export const setAbGroup = (group: 'A' | 'B') => {
  if (typeof window === 'undefined') return;

  const STORAGE_KEY = 'degging_ab_group';
  const currentGroup = localStorage.getItem(STORAGE_KEY);

  if (currentGroup !== group) {
    localStorage.setItem(STORAGE_KEY, group);
    // 그룹이 처음 배정되거나 변경되었을 때 이벤트 전송
    pushGtmEvent('ab_group_assigned', { ab_group: group });
  } else {
    // 이미 같은 그룹이면 '배정' 이벤트는 안 보내지만, 
    // GA4 세션에 다시 각인시키기 위해 단순 정보성 이벤트만 전송 (선택 사항)
    pushGtmEvent('ab_group_session_init', { ab_group: group });
  }
};

/**
 * 페이지 로드 시 현재 로컬에 저장된 A/B 그룹 정보를 GA4에 다시 알립니다.
 * 이를 통해 실시간 리포트에서 돌아온 사용자의 그룹을 항상 확인할 수 있습니다.
 */
export const initAbGroupTracking = () => {
  if (typeof window === 'undefined') return;
  
  const group = getAbGroup();
  if (group) {
    pushGtmEvent('ab_group_session_init', { ab_group: group });
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
