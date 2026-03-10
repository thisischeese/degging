"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { motion, AnimatePresence } from "framer-motion";
import Image from "next/image";
import splashImg from "@/assets/images/onboarding/splash1.png";

export default function OnboardingPage() {
  const router = useRouter();
  const [isVisible, setIsVisible] = useState(true);

  useEffect(() => {
    // 1초 동안 스플래시 노출
    const timer = setTimeout(() => {
      setIsVisible(false);
    }, 1000);

    return () => clearTimeout(timer);
  }, []);

  return (
    <AnimatePresence onExitComplete={() => router.push("/login")}>
      {isVisible && (
        <motion.div
          initial={{ opacity: 1 }}
          exit={{ opacity: 0, y: -100 }} // 위로 올라가며 사라지는 효과
          transition={{ duration: 0.8, ease: "easeInOut" }}
          className="fixed inset-0 z-50 bg-bg_white flex items-center justify-center"
        >
          {/* 피그마에서 추출한 통이미지 */}
          <div className="relative w-full h-full max-w-[430px] mx-auto">
            <Image
              src={splashImg} // ← 파일명 수정 완료!
              alt="Splash"
              fill
              priority
              className="object-contain" // 이미지 비율 유지
            />
          </div>
        </motion.div>
      )}
    </AnimatePresence>
  );
}
