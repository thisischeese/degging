"use client";

import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { SignupFormData } from "@/features/auth/types"; 
import StepEmail from "@/features/auth/components/StepEmail";
import StepPassword from "@/features/auth/components/StepPassword";
import StepNickname from "@/features/auth/components/StepNickname";
import StepTrend from "@/features/auth/components/StepTrend";
import StepMood from "@/features/auth/components/StepMood";
import StepLoading from "@/features/auth/components/StepLoading";
import StepWelcome from "@/features/auth/components/StepWelcome";

// API 호출 함수 추가
import { postSignup } from "@/features/auth/api/signupApi";

export default function SignupPage() {
  const [step, setStep] = useState(1);
  const [formData, setFormData] = useState<SignupFormData>({
    email: "",
    password: "",
    nickname: "",
    birthDate: "",
    trends: [], 
    moods: [],
  });
  
  const updateFormData = (newData: Partial<SignupFormData>) => {
    setFormData((prev) => ({ ...prev, ...newData }));
  };
  
  // 1단계: 회원가입 진행 (Step 3 완료 후 호출)
  const handleSignupRequest = async () => {
    try {
      const result = await postSignup(formData);
      // 성공 시 토큰 저장 로직이 필요할 수 있습니다 (axios_instance interceptor에서 처리 권장)
      console.log("회원가입 성공:", result);
      return true;
    } catch (error) {
      console.error("회원가입 실패:", error);
      alert("회원가입 중 오류가 발생했습니다.");
      return false;
    }
  };

  // 2단계: 온보딩 결과 제출 (Step 5 완료 후 호출)
  const handleOnboardingRequest = async () => {
    try {
      // [TODO] 온보딩 결과 제출 API 연결 (현재 명세서 작업 중)
      console.log("온보딩 데이터 제출:", { trends: formData.trends, moods: formData.moods });
      // 임시로 1.5초 대기 (로딩 체감)
      await new Promise(resolve => setTimeout(resolve, 1500));
      return true;
    } catch (error) {
      console.error("온보딩 실패:", error);
      return false;
    }
  };

  const nextStep = async () => {
    if (step === 3) {
      const success = await handleSignupRequest();
      if (!success) return; // 실패 시 다음 단계로 가지 않음
    }
    setStep((prev) => prev + 1);
  };


  return (
    <div className="flex flex-1 flex-col bg-bg_white min-h-0">
      {/* 1~3단계는 피그마 디자인에 따라 헤더 없이 진행 */}
      <main className="flex-1 min-h-0 flex flex-col px-6 py-8 relative">
        <AnimatePresence mode="wait">
          <motion.div
            key={step}
            initial={{ opacity: 0, x: 10 }}
            animate={{ opacity: 1, x: 0 }}
            exit={{ opacity: 0, x: -10 }}
            transition={{ duration: 0.3 }}
            className="flex-1 min-h-0 flex flex-col"
          >
            {step === 1 && <StepEmail next={nextStep} updateData={updateFormData} formData={formData} />}
            {step === 2 && <StepPassword next={nextStep} updateData={updateFormData} formData={formData} />}
            {step === 3 && <StepNickname next={nextStep} updateData={updateFormData} formData={formData} />}
            {step === 4 && <StepTrend next={nextStep} updateData={updateFormData} formData={formData} />}
            {step === 5 && <StepMood next={nextStep} updateData={updateFormData} formData={formData} />}
            {step === 6 && (
              <StepLoading 
                next={nextStep} 
                onSignup={async () => { await handleOnboardingRequest(); }}
              />
            )}
            {step === 7 && <StepWelcome formData={formData} />}
          </motion.div>
        </AnimatePresence>
      </main>
    </div>
  );
}