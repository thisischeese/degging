"use client";

import { useState } from "react";
import Image from "next/image";
import { Input } from "@/common/components/Input";
import Button from "@/common/components/Button";
import { SignupStepProps } from "../types";
import { postEmailVerificationRequest, postEmailVerificationConfirm } from "../api/emailApi";

export default function StepEmail({ next, updateData, formData }: SignupStepProps) {
  const [email, setEmail] = useState("");
  const [authCode, setAuthCode] = useState("");
  const [isEmailSent, setIsEmailSent] = useState(false);
  const [isVerified, setIsVerified] = useState(false);
  const [emailError, setEmailError] = useState("");
  const [authError, setAuthError] = useState("");
  const [isLoading, setIsLoading] = useState(false);

  const handleSendCode = async () => {
    if (!email.includes("@")) {
      setEmailError("올바른 이메일 형식이 아닙니다.");
      return;
    }
    
    setIsLoading(true);
    try {
      await postEmailVerificationRequest(email);
      setEmailError("");
      setIsEmailSent(true);
    } catch (error) {
      console.error(error);
      setEmailError("인증번호 발송에 실패했습니다.");
    } finally {
      setIsLoading(false);
    }
  };

  const handleCheckAuthOnly = async () => {
    if (!authCode) return;
    
    setIsLoading(true);
    try {
      await postEmailVerificationConfirm(email, authCode);
      setAuthError("인증번호가 확인되었습니다.");
      setIsVerified(true);
    } catch (error) {
      console.error(error);
      setAuthError("인증번호가 일치하지 않습니다.");
      setIsVerified(false);
    } finally {
      setIsLoading(false);
    }
  };

  const handleVerifyAndNext = () => {
    if (isVerified) {
      updateData({ email });
      next();
    } else {
      setAuthError("먼저 인증번호 확인을 완료해 주세요.");
    }
  };

  return (
    <div className="flex flex-col h-full">
      {/* 상단 Step 표시 */}
      <div className="flex justify-center gap-2 mt-4 mb-10">
        <div className="w-1.5 h-1.5 rounded-full bg-black" />
        <div className="w-1.5 h-1.5 rounded-full bg-gray-300" />
        <div className="w-1.5 h-1.5 rounded-full bg-gray-300" />
      </div>

      {/* 로고 영역 */}
      <div className="flex flex-col items-center mb-12">
        <Image src="/images/common/logo.png" alt="Logo" width={120} height={120} className="object-contain" />
      </div>

      {/* 입력 폼 영역 */}
      <div className="flex-1">
        <div className="h-[94px]">
          <Input
            label="이메일"
            placeholder="이메일 주소를 입력해 주세요."
            value={email}
            onChange={(e) => {
              setEmail(e.target.value);
              setEmailError("");
            }}
            error={emailError}
            rightElement={
              <Button 
                variant="gray" 
                size="sm" 
                onClick={handleSendCode} 
                disabled={!email || isLoading}
                className="w-[84px]"
              >
                {isEmailSent ? "재전송" : "이메일 인증"}
              </Button>
            }
          />
        </div>

        <div className="h-[94px] mt-4">
          <Input
            label="인증코드"
            placeholder="인증코드를 입력해 주세요."
            value={authCode}
            onChange={(e) => {
              setAuthCode(e.target.value);
              setAuthError(""); 
            }}
            error={authError}
            rightElement={
              <Button 
                variant="gray" 
                size="sm" 
                onClick={handleCheckAuthOnly}
                disabled={!isEmailSent || !authCode || isLoading || isVerified} 
                className="w-[60px]"
              >
                {isVerified ? "완료" : "확인"}
              </Button>
            }
          />
        </div>
      </div>

      {/* 하단 다음 버튼 */}
      <div className="pb-4 mt-2">
        <div className="min-h-[24px] mb-2 text-center">
        </div>
        <Button
          variant={isVerified ? "primary" : "gray"}
          size="full"
          disabled={!isVerified || isLoading} 
          onClick={handleVerifyAndNext}
          className="h-[52px] rounded-xl!"
        >
          다음 단계로
        </Button>
      </div>
    </div>
  );
}