"use client";

import Image from "next/image";
import { useRouter } from "next/navigation";
import Button from "@/common/components/Button";
import { SignupFormData } from "../types";

interface StepWelcomeProps {
  formData: SignupFormData;
}

export default function StepWelcome({ formData }: StepWelcomeProps) {
  const router = useRouter();

  // 로그인 페이지로 이동하거나, 자동으로 로그인 처리 후 메인으로 보낼 수 있습니다.
  const handleGoLogin = () => {
    router.push("/login");
  };

  return (
    <div className="flex flex-col h-full items-center justify-between py-16">
      <div className="flex-1 flex flex-col items-center justify-center text-center">
        {/* 1. 중앙 원형 아이콘 영역 */}
        <div className="relative w-48 h-48 mb-12 rounded-full bg-[#FDFBF6] flex items-center justify-center shadow-sm border border-gray-100">
          <Image
            src="/images/auth/welcome.png"
            alt="Welcome Cake"
            width={120}
            height={120}
            className="object-contain"
          />
        </div>

        {/* 2. 환영 메시지 영역 */}
        <div className="space-y-4">
          <h1 className="text-3xl font-black text-gray-900 tracking-tight font-pretendard">
            WELCOME
          </h1>
          
          <div className="text-2xl font-bold text-gray-800 font-pretendard leading-snug">
            <span className="text-[#C3304F]">{formData.nickname || "회원"}</span>님<br />
            회원가입을 축하합니다
          </div>

          <p className="text-sm text-gray-500 font-medium font-pretendard leading-relaxed px-10">
            로그인하고 내 주변에 숨어있는<br />
            더 많은 디저트를 추천 받아보세요!
          </p>
        </div>
      </div>

      {/* 3. 하단 버튼 영역 */}
      <div className="w-full pb-4 px-6 mt-2">
        <Button
          variant="primary"
          size="full"
          onClick={handleGoLogin}
          className="bg-[#C3304F]! text-white!"
        >
          로그인하기
        </Button>
      </div>
    </div>
  );
}