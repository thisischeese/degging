import Image from "next/image";
import { useRouter } from "next/navigation";

import { ReviewItem as ReviewItemType } from "@/features/users/types";

// ─────────────────────────────────────────────────────────
// Props 설명:
// - ReviewItemType 타입을 그대로 props로 받습니다.
//   (reviewId, cafeId, cafeName, cafeImageUrl, content, createdAt)
// ─────────────────────────────────────────────────────────
export default function ReviewItem({
  reviewId,
  cafeId,
  cafeName,
  cafeImageUrl,
  content,
  createdAt,
}: ReviewItemType) {
  const router = useRouter();

  const handleClick = () => {
    router.push(`/cafes/${cafeId}/reviews/${reviewId}`);
  };

  return (
    <div
      className="flex items-center gap-4 bg-white rounded-2xl p-4 cursor-pointer active:scale-[0.99] transition-transform border border-gray-100 shadow-sm"
      onClick={handleClick}
    >
      {/* 
        1. 왼쪽 카페 썸네일 이미지 
        - 피그마 참고: 정사각형 (약 64x64), 둥근 모서리
        - w-[64px] h-[64px]: 너비와 높이 딱 64px로 고정
        - rounded-xl: 귀여운 둥근 모서리
        - overflow-hidden: 이미지가 모서리 밖으로 삐져나오지 않게 잘라줌
        - shrink-0: 다른 요소가 많아져도 이미지 크기가 찌그러지지 않게 방지
      */}
      <div className="relative w-[64px] h-[64px] rounded-xl overflow-hidden shrink-0">
        <Image
          src={cafeImageUrl}
          alt={`${cafeName} 썸네일`}
          fill // 부모(relative 박스)를 꽉 채우는 next/image 특수 옵션
          className="object-cover" // 이미지 비율을 유지하며 박스를 꽉 채움 (잘릴 수 있음)
        />
      </div>

      {/* 
        2. 오른쪽 텍스트 영역 (카페명, 리뷰 미리보기, 날짜)
        - min-w-0: flex 컨테이너 안에서 텍스트가 제대로 말줄임(...)되도록 하는 필수 설정
      */}
      <div className="flex flex-col flex-1 min-w-0 gap-1 font-pretendard">
        {/* 카페 이름 */}
        <p className="text-[14px] font-semibold text-gray-900 truncate">
          {cafeName}
        </p>

        {/* 
          리뷰 본문 미리보기 
          - truncate: 텍스트가 박스보다 길면 "하 진짜 너무 맛있었음 친구들이..." 처럼 뒤를 ...으로 잘라줌
        */}
        <p className="text-[13px] text-gray-500 truncate">
          {content}
        </p>

        {/* 
          작성 날짜 
          - 피그마에서 오른쪽 하단 끝에 붙어있음 → text-right로 오른쪽 정렬
        */}
        <p className="text-[11px] text-gray-400 text-right">
          {createdAt}
        </p>
      </div>
    </div>
  );
}
