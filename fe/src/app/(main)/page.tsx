"use client";

import Header from "@/common/components/Header";
import BottomNav from "@/common/components/BottomNav";

export default function Home() {
  return (
    // 전체를 flex-col로 잡고 높이를 100vh(min-h-screen)로 설정합니다.
    <div className="flex min-h-screen flex-col bg-bg_white font-pretendard">
      
      {/* 1. 상단 헤더 영역 */}
      <Header 
        centerContent="Degging" 
        rightContent={<button className="text-xs">설정</button>}
      />

      {/* 2. 중앙 컨텐츠 영역 */}
      {/* pb-20을 주어 하단 탭바에 컨텐츠가 가려지지 않게 합니다. */}
      <main className="flex-1 px-4 py-6 pb-20">
        <section className="mb-8">
          <h2 className="mb-4 text-xl font-bold">오늘의 큐레이션</h2>
          <div className="h-48 w-full rounded-2xl bg-gray-200 flex items-center justify-center text-gray-500">
            큐레이션 카드 들어갈 자리 (준비 중)
          </div>
        </section>

        <section>
          <h2 className="mb-4 text-xl font-bold">실시간 디저트 랭킹</h2>
          <ul className="flex flex-col gap-4">
            {[1, 2, 3, 4, 5].map((num) => (
              <li key={num} className="flex items-center gap-4 border-b border-gray-100 pb-2">
                <span className="font-bold text-primary_btn_red">{num}</span>
                <span className="text-gray-700">인기 검색어 {num}위</span>
              </li>
            ))}
          </ul>
        </section>
      </main>

      {/* 3. 하단 내비게이션 영역 */}
      <BottomNav />
      
    </div>
  );
}