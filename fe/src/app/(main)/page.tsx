'use client';

import Header from "@/common/components/Header";
import BottomNav from "@/common/components/BottomNav";
import Button from "@/common/components/Button"; // 아까 만든 버튼 컴포넌트

export default function Home() {
  return (
    <div className="flex min-h-screen flex-col bg-bg_white font-pretendard">
      <Header centerContent="Degging 버튼 테스트" />

      <main className="flex-1 px-4 py-6 pb-20 space-y-10">
        
        {/* 1. Auth 화면용 (긴 버튼) */}
        <section>
          <h2 className="mb-4 text-lg font-bold border-b pb-2">1. Auth (Full Size)</h2>
          <div className="flex flex-col gap-3">
            <Button variant="primary" size="full">로그인 (활성화)</Button>
            <Button variant="primary" size="full" disabled>로그인 (비활성화/회색)</Button>
            <Button variant="kakao" size="full">카카오 로그인 (노랑)</Button>
            <Button variant="black" size="full">애플 로그인 (검정)</Button>
          </div>
        </section>

        {/* 2. 작은 기능 버튼 (인증/중복확인) */}
        <section>
          <h2 className="mb-4 text-lg font-bold border-b pb-2">2. Auth 서브 버튼 (Small)</h2>
          <div className="flex items-center gap-4">
            <p className="text-sm text-gray-600">이메일 중복 검사:</p>
            <Button variant="gray" size="sm">중복확인</Button>
          </div>
          <div className="flex items-center gap-4 mt-2">
            <p className="text-sm text-gray-600">인증 코드 전송:</p>
            <Button variant="gray" size="sm">인증요청</Button>
          </div>
        </section>

        {/* 3. 팝업 / 모달용 (중간 크기) */}
        <section>
          <h2 className="mb-4 text-lg font-bold border-b pb-2">3. 팝업/모달 (Medium)</h2>
          <div className="flex gap-4 justify-center bg-white p-6 rounded-2xl shadow-sm">
            <Button variant="gray" size="md">취소</Button>
            <Button variant="primary" size="md">확인</Button>
          </div>
        </section>

        {/* 4. 스크랩/기타 (하얀 배경) */}
        <section>
          <h2 className="mb-4 text-lg font-bold border-b pb-2">4. 스크랩/필터 (Outline)</h2>
          <div className="flex gap-2">
            <Button variant="outline" size="sm">최신순</Button>
            <Button variant="outline" size="sm">거리순</Button>
            <Button variant="outline" size="sm" className="text-primary_btn_red font-bold">인기순</Button>
          </div>
        </section>

      </main>

      <BottomNav />
    </div>
  );
}