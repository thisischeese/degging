import { create } from 'zustand';

interface MapState {
  // 필터 상태 유지 관리
  selectedFilters: string[];
  toggleFilter: (filter: string) => void;

  // 현재 사용자 위치
  userLocation: { lat: number; lng: number } | null;
  setUserLocation: (location: { lat: number; lng: number }) => void;

  // 위치 추적 상태
  isTracking: boolean;
  toggleTracking: () => void;
  setTracking: (isTracking: boolean) => void;
}

export const useMapStore = create<MapState>((set) => ({
  selectedFilters: [],
  toggleFilter: (filter: string) =>
    set((state) => ({
      selectedFilters: state.selectedFilters.includes(filter)
        ? state.selectedFilters.filter((f) => f !== filter)
        : [...state.selectedFilters, filter],
    })),
  userLocation: null,
  setUserLocation: (userLocation) => set({ userLocation }),
  isTracking: false,
  toggleTracking: () => set((state) => ({ isTracking: !state.isTracking })),
  setTracking: (isTracking) => set({ isTracking }),
}));
