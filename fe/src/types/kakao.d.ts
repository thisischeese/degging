export {};

declare global {
  interface Window {
    kakao: typeof kakao;
  }

  namespace kakao.maps {
    // 1. 지도 인스턴스 관련
    class Map {
      constructor(container: HTMLElement, options: MapOptions);
      setCenter(latlng: LatLng): void;
      panTo(latlng: LatLng): void;
      getLevel(): number;
      setLevel(level: number, options?: { animate?: boolean | { duration: number }; anchor?: LatLng }): void;
      relayout(): void;
    }

    interface MapOptions {
      center: LatLng;
      level?: number;
      mapTypeId?: MapTypeId;
      draggable?: boolean;
      scrollwheel?: boolean;
    }

    // 2. 좌표 및 크기 관련
    class LatLng {
      constructor(latitude: number, longitude: number);
      getLat(): number;
      getLng(): number;
    }

    class Size {
      constructor(width: number, height: number);
    }

    class Point {
      constructor(x: number, y: number);
    }

    // 3. 마커 관련
    class Marker {
      constructor(options: MarkerOptions);
      setMap(map: Map | null): void;
      getMap(): Map | null;
      setPosition(position: LatLng): void;
      getPosition(): LatLng;
      setZIndex(zIndex: number): void;
      getZIndex(): number;
      setImage(image: MarkerImage): void;
      getImage(): MarkerImage | null;
      setTitle(title: string): void;
      getTitle(): string;
    }

    interface MarkerOptions {
      map?: Map;
      position: LatLng;
      image?: MarkerImage;
      title?: string;
      draggable?: boolean;
      clickable?: boolean;
      zIndex?: number;
    }

    class MarkerImage {
      constructor(src: string, size: Size, options?: MarkerImageOptions);
    }

    interface MarkerImageOptions {
      alt?: string;
      coords?: string;
      offset?: Point;
      spriteOrigin?: Point;
      spriteSize?: Size;
    }

    // 4. 커스텀 오버레이 관련
    class CustomOverlay {
      constructor(options: CustomOverlayOptions);
      setMap(map: Map | null): void;
      getMap(): Map | null;
      setPosition(position: LatLng): void;
      getPosition(): LatLng;
      setContent(content: HTMLElement | string): void;
      getContent(): HTMLElement | string;
      setZIndex(zIndex: number): void;
      getZIndex(): number;
    }

    interface CustomOverlayOptions {
      map?: Map;
      position: LatLng;
      content: HTMLElement | string;
      clickable?: boolean;
      xAnchor?: number;
      yAnchor?: number;
      zIndex?: number;
    }

    // 5. 이벤트 및 유틸리티
    namespace event {
      function addListener(target: Map | Marker | CustomOverlay, type: string, callback: () => void): void;
      function removeListener(target: Map | Marker | CustomOverlay, type: string, callback: () => void): void;
    }

    enum MapTypeId {
      ROADMAP = 1,
      SKYVIEW = 2,
      HYBRID = 3,
    }

    function load(callback: () => void): void;
  }
}