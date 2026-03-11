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
import { postSignup } from "@/features/auth/api/signup";

export default function SignupPage() {
  const [step, setStep] = useState(1);
  const [formData, setFormData] = useState<SignupFormData>({
    email: "",
    password: "",
    nickname: "",
    birth: "",
    trends: [], 
    moods: [],
  });
  

  const updateFormData = (newData: Partial<SignupFormData>) => {
    setFormData((prev) => ({ ...prev, ...newData }));
  };
  
  // 실제로 가입을 진행할 함수
  const handleSignupRequest = async () => {
    // postSignup 함수에 지금껏 모은 formData를 넣어서 실행!
    await postSignup(formData); 
  };

  const nextStep = () => setStep((prev) => prev + 1);
  const prevStep = () => setStep((prev) => prev - 1);

  return (
    <div className="flex min-h-screen flex-col bg-bg_white">
      {/* 1~3단계는 피그마 디자인에 따라 헤더 없이 진행 */}
      <main className="flex-1 flex flex-col px-6 py-8 relative overflow-hidden">
        <AnimatePresence mode="wait">
          <motion.div
            key={step}
            initial={{ opacity: 0, x: 10 }}
            animate={{ opacity: 1, x: 0 }}
            exit={{ opacity: 0, x: -10 }}
            transition={{ duration: 0.3 }}
            className="flex-1 flex flex-col"
          >
            {step === 1 && <StepEmail next={nextStep} updateData={updateFormData} formData={formData} />}
            {step === 2 && <StepPassword next={nextStep} updateData={updateFormData} formData={formData} />}
            {step === 3 && <StepNickname next={nextStep} updateData={updateFormData} formData={formData} />}
            {step === 4 && <StepTrend next={nextStep} updateData={updateFormData} formData={formData} />}
            {step === 5 && <StepMood next={nextStep} updateData={updateFormData} formData={formData} />}
            {step === 6 && <StepLoading next={nextStep} onSignup={handleSignupRequest}/>}
            {step === 7 && <StepWelcome formData={formData} />}
          </motion.div>
        </AnimatePresence>
      </main>
    </div>
  );
}