"use client";

import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { SignupFormData, SignupRequest } from "@/features/auth/types"; 
import StepEmail from "@/features/auth/components/StepEmail";
import StepPassword from "@/features/auth/components/StepPassword";
import StepNickname from "@/features/auth/components/StepNickname";
import StepTrend from "@/features/auth/components/StepTrend";
import StepMood from "@/features/auth/components/StepMood";
import StepLoading from "@/features/auth/components/StepLoading";
import StepWelcome from "@/features/auth/components/StepWelcome";
import Modal from "@/common/components/Modal";
import Button from "@/common/components/Button";


// API 호출 함수 추가
import { postSignup } from "@/features/auth/api/signupApi";
import { postLogin } from "@/features/auth/api/loginApi";
import { postOnboardingResults } from "@/features/onboarding/api/onboardingApi";
import { OnboardingResult } from "@/features/onboarding/types";

export default function SignupPage() {
  const [step, setStep] = useState(1);
  const [formData, setFormData] = useState<SignupFormData>({
    email: "",
    password: "",
    nickname: "",
    birthDate: "",
    gender: "MALE",
    trends: [],
    moods: [],
  });

  const [dialog, setDialog] = useState<{ isOpen: boolean; title: string; message?: string }>({
    isOpen: false,
    title: "",
  });

  const showAlert = (title: string, message?: string) => {
    setDialog({ isOpen: true, title, message });
  };
  
  const updateFormData = (newData: Partial<SignupFormData>) => {
    setFormData((prev) => ({ ...prev, ...newData }));
  };
  
  // 1단계: 회원가입 진행 (Step 3 완료 후 호출)
  const handleSignupRequest = async (currentData: SignupFormData) => {
    try {
      // 명세서에 맞는 데이터 전송 (name 없이 진행)
      const signupData: SignupRequest = {
        email: currentData.email,
        password: currentData.password,
        nickname: currentData.nickname,
        gender: currentData.gender as "MALE" | "FEMALE",
        birthDate: currentData.birthDate,
      };

      const result = await postSignup(signupData);
      
      // 숫자 200과 문자열 "200" 모두 처리
      if (String(result.code) === "200") {
        console.log("회원가입 성공:", result.message);
        
        // 1. 회원가입 응답에서 onboardingToken 추출 (타입 안전성 확보)
        const token = result.data?.onboardingToken;

        if (token) {
          // 백엔드 레퍼런스 코드에 맞춰 sessionStorage에 저장
          sessionStorage.setItem("ONBOARDING_TOKEN", token);
          console.log("Onboarding Token 세션 저장 완료!");
        } else {
          // 2. 만약 onboardingToken이 명세와 달리 안 들어왔다면 기존 자동 로그인(폴백) 시도
          try {
            await postLogin({
              email: currentData.email,
              password: currentData.password,
            });
            console.log("회원가입 후 자동 로그인 성공 (대체 토큰 발급 완료)");
          } catch (loginError) {
            console.error("자동 로그인 실패:", loginError);
          }
        }

        return true;
      } else {
        showAlert(result.message || "회원가입에 실패했습니다.");
        return false;
      }
    } catch (error) {
      console.error("회원가입 실패:", error);
      showAlert("회원가입 중 오류가 발생했습니다.");
      return false;
    }
  };

  // 2단계: 온보딩 결과 제출 (Step 6 직전 호출)
  const handleOnboardingRequest = async (currentData?: SignupFormData) => {
    try {
      const dataToUse = currentData || formData;
      const token = sessionStorage.getItem("ONBOARDING_TOKEN") || "";

      const onboardingData: OnboardingResult = {
        onboardingToken: token,
        cafeIds: dataToUse.moods, // string[]
        menuIds: dataToUse.trends.map(id => Number(id)), // number[] 변환
      };

      await postOnboardingResults(onboardingData);
      
      // 온보딩 완료 시 임시 토큰 즉시 파기
      sessionStorage.removeItem("ONBOARDING_TOKEN");
      
      return true;
    } catch (error) {
      console.error("온보딩 실패:", error);
      return false;
    }
  };

  const nextStep = async (stepData?: unknown) => {
    let currentData = formData;
    // 이벤트 객체가 아닌 순수 데이터(Partial<SignupFormData>)인 경우에만 병합
    if (stepData && typeof stepData === "object") {
      const isEvent = "nativeEvent" in stepData;
      if (!isEvent) {
        currentData = { ...formData, ...(stepData as Partial<SignupFormData>) };
        setFormData(currentData); // 상태 갱신 추가!
      }
    }

    if (step === 3) {
      const success = await handleSignupRequest(currentData);
      if (!success) return; // 실패 시 다음 단계로 가지 않음
    }
    setStep((prev) => prev + 1);
  };


  console.log(`[SignupPage Render] Step: ${step}`, formData);

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
            {step === 1 && <StepEmail next={nextStep} updateData={updateFormData} formData={formData} onAlert={showAlert} />}
            {step === 2 && <StepPassword next={nextStep} updateData={updateFormData} formData={formData} />}
            {step === 3 && <StepNickname next={nextStep} updateData={updateFormData} formData={formData} />}
            {step === 4 && <StepTrend next={nextStep} updateData={updateFormData} formData={formData} />}
            {step === 5 && <StepMood next={nextStep} updateData={updateFormData} formData={formData} />}
            {step === 6 && (
              <StepLoading 
                next={nextStep} 
                onSignup={async () => {
                   // 상태 업데이트 지연 방지를 위해 명시적으로 formData를 넘김
                   await handleOnboardingRequest(formData); 
                }}
              />
            )}
            {step === 7 && <StepWelcome formData={formData} />}
          </motion.div>
        </AnimatePresence>
      </main>

      {/* 알럿용 모달 */}
      <Modal isOpen={dialog.isOpen} onClose={() => setDialog(prev => ({ ...prev, isOpen: false }))} size="sm">
        <div className="flex flex-col items-center gap-6 py-2">
          <div className="flex flex-col items-center gap-2 text-center">
            <span className="text-4xl mb-2">💡</span>
            <h2 className="text-[16px] font-bold text-gray-900 leading-snug whitespace-pre-wrap break-keep">{dialog.title}</h2>
            {dialog.message && (
              <p className="text-[13px] text-gray-500 font-medium leading-relaxed">{dialog.message}</p>
            )}
          </div>
          <Button variant="primary" size="full" onClick={() => setDialog(prev => ({ ...prev, isOpen: false }))} className="h-[52px] rounded-xl!">
            확인
          </Button>
        </div>
      </Modal>
    </div>
  );
}