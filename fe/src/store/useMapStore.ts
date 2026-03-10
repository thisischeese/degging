import { create } from 'zustand';

interface MapState {
  // 필터 상태 유지 관리
  selectedFilters: string[];
  toggleFilter: (filter: string) => void;

  // 현재 사용자 위치
  userLocation: { lat: number; lng: number } | null;
  setUserLocation: (location: { lat: number; lng: number }) => void;
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
}));
