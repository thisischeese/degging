"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { motion, AnimatePresence } from "framer-motion";
import Image from "next/image";
import Button from "@/common/components/Button";

// 이미지 경로 확인 필요
import splashImg from "@/assets/images/onboarding/splash1.png";
import logoImg from "@/assets/images/common/logo.png";

export default function OnboardingPage() {
  const router = useRouter();
  const [showSplash, setShowSplash] = useState(true);

  useEffect(() => {
    const timer = setTimeout(() => {
      setShowSplash(false);
    }, 3000); // 3초 대기
    return () => clearTimeout(timer);
  }, []);

  const POINT_COLOR = "#C6964D";

  return (
    <div className="relative w-full h-screen bg-bg_white overflow-hidden">
      {/* 1. 스플래시 화면 (전체 화면, 위로 사라짐) */}
      <AnimatePresence>
        {showSplash && (
          <motion.div
            key="splash"
            initial={{ y: 0 }}
            exit={{ y: "-100%" }}
            transition={{ duration: 0.6, ease: "easeInOut" }}
            className="absolute inset-0 z-50 w-full h-full"
          >
            <Image
              src={splashImg}
              alt="Splash"
              fill
              style={{ objectFit: "cover" }}
              priority
            />
          </motion.div>
        )}
      </AnimatePresence>

      {/* 2. 로그인/회원가입 메인 컨텐츠 */}
      <div className="relative w-full h-full flex flex-col items-center">
        {/* 상단 이미지 영역 (비워둠) */}
        <div className="w-full h-[50%]" />

        {/* 하단 컨텐츠 영역 (중앙부터 시작) */}
        <div className="flex flex-col items-center w-full px-8 flex-1">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: showSplash ? 0 : 1, y: 0 }}
            transition={{ delay: 0.5 }}
            className="flex flex-col items-center w-full"
          >
            {/* 로고 및 텍스트 */}
            <Image src={logoImg} alt="Logo" width={90} height={90} className="mb-4" />
            <h1 style={{ color: POINT_COLOR }} className="font-bold text-3xl mb-1 tracking-tight">
              Dessert Digging
            </h1>
            <p style={{ color: POINT_COLOR }} className="text-sm font-medium mb-12">
              맛있는 트렌드를 디깅하세요
            </p>

            {/* 버튼 섹션 */}
            <div className="w-full max-w-[300px] space-y-3">
              <Button
                variant="brown" // tailwind.config.ts에 등록한 brown 사용
                size="full"
                onClick={() => router.push("/signup")}
                className="!bg-primary_btn_brown" // !중요도로 갈색 강제 적용
              >
                회원가입
              </Button>

              <Button
                variant="gray"
                size="full"
                onClick={() => router.push("/login")}
                className="!text-[#444]"
              >
                로그인
              </Button>

              <p className="text-[10px] text-gray-400 text-center mt-6 leading-tight">
                계속 진행하면 Degging 서비스에서 개인위치정보를 수집하고 활용하는<br />
                것에 동의하는 것으로 간주됩니다.
              </p>
            </div>
          </motion.div>
        </div>
      </div>
    </div>
  );
}