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

  const handleGoLogin = () => {
    router.push("/login");
  };

  return (
    <div className="flex flex-col flex-1 min-h-0 -mx-6 -mt-8">

      {/* 중앙 콘텐츠 */}
      <div className="flex-1 min-h-0 flex flex-col items-center justify-center text-center px-6">
        {/* 원형 아이콘 */}
        <div className="relative w-44 h-44 mb-10 rounded-full bg-[#FDFBF6] flex items-center justify-center shadow-sm border border-gray-100">
          <Image
            src="/images/auth/welcome.png"
            alt="Welcome Cake"
            width={110}
            height={110}
            className="object-contain"
          />
        </div>

        {/* 환영 메시지 */}
        <div className="space-y-3">
          <h1 className="text-3xl font-black text-gray-900 tracking-tight font-pretendard">
            WELCOME
          </h1>
          <div className="text-2xl font-bold text-gray-800 font-pretendard leading-snug">
            <span className="text-[#C3304F]">{formData.nickname || "회원"}</span>님<br />
            회원가입을 축하합니다
          </div>
          <p className="text-sm text-gray-500 font-medium font-pretendard leading-relaxed px-8 pt-1">
            로그인하고 내 주변에 숨어있는<br />
            더 많은 디저트를 추천 받아보세요!
          </p>
        </div>
      </div>

      {/* 하단 버튼 — 다른 스텝과 동일한 구조 */}
      <div className="shrink-0 px-6 pt-3 pb-4 border-t border-gray-100">
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