"use client";

import { useEffect, useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import Image from "next/image";
import Button from "@/common/components/Button";
import splashImg from "@/assets/images/onboarding/splash1.png";
import logoImg from "@/assets/images/common/logo.png";

export default function OnboardingPage() {
  const [stage, setStage] = useState<"splash" | "auth">("splash");

  useEffect(() => {
    const timer = setTimeout(() => setStage("auth"), 1500);
    return () => clearTimeout(timer);
  }, []);

  const POINT_COLOR = "#C6964D";

  return (
    <div className="relative w-full h-screen bg-bg_white flex justify-center overflow-hidden">
      <AnimatePresence mode="sync">
        {/* 1. 스플래시 화면: 천천히 위로 올라가며 사라짐 */}
        {stage === "splash" && (
          <motion.div
            key="splash"
            initial={{ y: 0, opacity: 1 }}
            exit={{ 
              y: "-30%", // 너무 많이 올리지 않고 살짝만 올림
              opacity: 0, 
              transition: { duration: 1.2, ease: [0.22, 1, 0.36, 1] } // 속도 늦춤 + 부드러운 곡선
            }}
            className="fixed inset-0 z-50 w-full h-full max-w-[430px] mx-auto overflow-hidden"
          >
            <Image src={splashImg} alt="Splash" fill className="object-cover" priority />
          </motion.div>
        )}

        {/* 2. 로그인/회원가입 섹션: 스플래시가 나갈 때 천천히 나타남 */}
        {stage === "auth" && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: stage === "auth" ? 1 : 0 }}
            transition={{ duration: 1 }}
            className="relative w-full h-full max-w-[430px] mx-auto flex flex-col items-center"
          >
            <div className="w-full h-[50%]" />
            <div className="flex flex-col items-center w-full px-8 flex-1">
              <Image src={logoImg} alt="Logo" width={90} height={90} className="mb-4" />
              <h1 style={{ color: POINT_COLOR }} className="font-bold text-3xl mb-1 tracking-tight">
                Dessert Digging
              </h1>
              <p style={{ color: POINT_COLOR }} className="text-sm font-medium mb-12">
                맛있는 트렌드를 디깅하세요
              </p>

              <div className="w-full max-w-[300px] space-y-3">
                <Button variant="brown" size="full" className="!bg-primary_btn_brown">
                  회원가입
                </Button>
                <Button variant="gray" size="full" className="!text-[#444]">
                  로그인
                </Button>
                <p className="text-[10px] text-gray-400 text-center mt-6">
                  계속 진행하면 Degging 서비스에서 개인위치정보를 수집하고 활용하는 것에 동의하는 것으로 간주됩니다.
                </p>
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}