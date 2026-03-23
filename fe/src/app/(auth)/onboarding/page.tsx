"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { motion } from "framer-motion";
import Image from "next/image";
import Button from "@/common/components/Button";
import { pushGtmEvent } from "@/lib/abTest";

// 개별 사진 배치 데이터 (디자인 시안 콜라주 레이아웃 기반)
const PHOTOS = [
  {
    src: "/images/onboarding/onboard_coffee.webp",
    alt: "커피와 크로와상",
    style: { top: "0%", left: "0%", width: "34%", height: "50%" }
  },
  {
    src: "/images/onboarding/onboard_dessert.webp",
    alt: "디저트",
    style: { top: "93%", right: "-7%", width: "30%", height: "20%" },
    rotate: 0,
  },
  {
    src: "/images/onboarding/onboard_dujjon.webp",
    alt: "두쫀쿠",
    style: { top: "0%", right: "0%", width: "35%", height: "22%" }
  },
  {
    src: "/images/onboarding/onboard_chu.webp",
    alt: "츄러스",
    style: { top: "85%", left: "-5%", width: "30%", height: "39%" }
  },
  {
    src: "/images/onboarding/onboard_ice.webp",
    alt: "아이스크림",
    style: { top: "49%", right: "5%", width: "28%", height: "24%" }
  },
  {
    src: "/images/onboarding/onboard_bagle.webp",
    alt: "베이글",
    style: { top: "30%", right: "26%", width: "45%", height: "60%" }
  },
];

// 개별 사진 등장 애니메이션
const photoVariants = {
  hidden: (i: number) => ({
    opacity: 0,
    y: 40,
    scale: 0.85,
    rotate: PHOTOS[i]?.rotate ?? 0,
  }),
  visible: (i: number) => ({
    opacity: 1,
    y: 0,
    scale: 1,
    rotate: PHOTOS[i]?.rotate ?? 0,
    transition: {
      type: "spring" as const,
      damping: 26,
      stiffness: 120,
      delay: i * 0.25 + 0.2, // 0.25초 간격으로 순차 등장
    },
  }),
};

// 로고 등장 애니메이션
const logoVariants = {
  hidden: { opacity: 0, y: 20, scale: 0.9 },
  visible: {
    opacity: 1,
    y: 0,
    scale: 1,
    transition: {
      type: "spring" as const,
      damping: 28,
      stiffness: 150,
      delay: PHOTOS.length * 0.25 + 0.6, // 사진 등장 완료 후
    },
  },
};

const POINT_COLOR = "#C6964D";

// 버튼 등장 딜레이 (사진 등장 + 로고 등장 완료 후)
const BUTTONS_DELAY = PHOTOS.length * 0.25 + 0.6 + 0.8;

export default function OnboardingPage() {
  const router = useRouter();
  const [showButtons, setShowButtons] = useState(false);

  useEffect(() => {
    // BUTTONS_DELAY는 초(s) 단위이므로 밀리초(ms)로 변환
    const timer = setTimeout(() => {
      setShowButtons(true);
    }, BUTTONS_DELAY * 1000);
    return () => clearTimeout(timer);
  }, []);

  return (
    <div className="relative w-full h-screen bg-bg_white overflow-hidden flex flex-col items-center">
      {/* 사진 콜라주 영역 */}
      <div className="relative w-full" style={{ height: "55%" }}>
        {PHOTOS.map((photo, i) => (
          <motion.div
            key={photo.src}
            custom={i}
            variants={photoVariants}
            initial="hidden"
            animate="visible"
            className="absolute overflow-hidden rounded-lg shadow-md"
            style={{
              ...photo.style,
            }}
          >
            <Image
              src={photo.src}
              alt={photo.alt}
              fill
              className="object-cover"
              sizes="50vw"
              priority
            />
          </motion.div>
        ))}
      </div>

      {/* 로고 + 텍스트 + 버튼 */}
      <motion.div
        variants={logoVariants}
        initial="hidden"
        animate="visible"
        className="flex flex-col items-center mt-4"
      >
        <Image
          src="/images/common/logo.png"
          alt="Logo"
          width={70}
          height={70}
          className="mb-3"
        />
        <h1
          style={{ color: POINT_COLOR }}
          className="font-bold text-2xl mb-1 tracking-tight"
        >
          Dessert Digging
        </h1>
        <p
          style={{ color: POINT_COLOR }}
          className="text-sm font-medium"
        >
          맛있는 트렌드를 디깅하세요
        </p>
      </motion.div>

      {/* 버튼 섹션 (showButtons가 true가 된 후 렌더링되면서 페이드인) */}
      {showButtons && (
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{
            type: "spring" as const,
            stiffness: 200, // 더 천천히 올라오도록 (기존 300)
            damping: 20,
            opacity: { duration: 1.2 }, // 페이드인 지속 시간 증가 (기존 0.4)
          }}
          className="flex flex-col items-center w-full px-8 mt-8"
        >
          <div className="w-full max-w-[300px] space-y-3">
            <Button
              variant="brown"
              size="full"
              onClick={() => {
                pushGtmEvent("onboarding_action", { type: "signup" });
                router.push("/signup");
              }}
              className="!bg-primary_btn_brown"
            >
              회원가입
            </Button>

            <Button
              variant="gray"
              size="full"
              onClick={() => {
                pushGtmEvent("onboarding_action", { type: "login" });
                router.push("/login");
              }}
              className="!text-[#444]"
            >
              로그인
            </Button>

            <p className="text-[10px] text-gray-400 text-center mt-3 leading-tight">
              계속 진행하면 Degging 서비스에서 개인위치정보를 수집하고 활용하는
              <br />
              것에 동의하는 것으로 간주됩니다.
            </p>
          </div>
        </motion.div>
      )}
    </div>
  );
}