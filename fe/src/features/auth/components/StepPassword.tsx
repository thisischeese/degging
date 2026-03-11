"use client";

import { useState } from "react";
import Image from "next/image";
import { Input } from "@/common/components/Input";
import Button from "@/common/components/Button";
import { SignupStepProps } from "../types";
import logoImg from "@/assets/images/common/logo.png";

export default function StepPassword({ next, updateData }: SignupStepProps) {
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [passwordError, setPasswordError] = useState("");

  // 규칙: 영어 + 숫자 + 특수문자 조합, 8~16자
  const passwordRegex = /^(?=.*[a-zA-Z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]{8,16}$/;

  // 실시간 검증 변수
  const isPasswordValid = passwordRegex.test(password);
  const isPasswordMatch = confirmPassword.length > 0 && password === confirmPassword;

  // 에러 메시지 처리 
  const confirmErrorMessage = 
    confirmPassword.length > 0 && !isPasswordMatch ? "비밀번호가 일치하지 않습니다." : "";

  const handleNext = () => {
    // 1. 규칙 검사
    if (!isPasswordValid) {
      setPasswordError("8~16자 이내의 영어 + 특수문자 + 숫자 조합으로 해주세요.");
      return;
    }
    // 2. 일치 검사
    if (!isPasswordMatch) return;

    // 성공 시 데이터 업데이트 및 다음 이동
    updateData({ password });
    next();
  };

  return (
    <div className="flex flex-col h-full">
      {/* 상단 Step 표시 - 두 번째 단계 활성화 */}
      <div className="flex justify-center gap-2 mt-4 mb-10">
        <div className="w-1.5 h-1.5 rounded-full bg-gray-300" />
        <div className="w-1.5 h-1.5 rounded-full bg-black" />
        <div className="w-1.5 h-1.5 rounded-full bg-gray-300" />
      </div>

      {/* 로고 영역 (이메일 화면과 동일한 mb-12) */}
      <div className="flex flex-col items-center mb-12">
        <Image src={logoImg} alt="Logo" width={120} height={120} className="object-contain" />
      </div>

      {/* 입력 폼 영역 (이메일 화면과 동일한 flex-1 구조) */}
      <div className="flex-1">
        {/* 비밀번호 입력 섹션 (h-[94px]) */}
        <div className="h-[94px]">
          <Input
            label="비밀번호"
            type="password"
            placeholder="비밀번호를 입력해 주세요."
            value={password}
            onChange={(e) => {
              setPassword(e.target.value);
              setPasswordError(""); // 입력 시작하면 에러 지움
            }}
            error={passwordError}
          />
        </div>

        {/* 비밀번호 확인 입력 섹션 (h-[94px], mt-4 간격) */}
        <div className="h-[94px] mt-4">
          <Input
            label="비밀번호 확인"
            type="password"
            placeholder="비밀번호를 다시 입력해 주세요."
            value={confirmPassword}
            onChange={(e) => setConfirmPassword(e.target.value)}
            error={confirmErrorMessage}
          />
        </div>
      </div>

      {/* 하단 다음 버튼 (mt-44 적용하여 이메일 화면과 높이 통일)*/} 
      <div className="pb-4 mt-44">
        {/* <Button
          variant="gray"
          size="full"
          // 규칙과 일치가 모두 확인되어야 버튼 활성화
          disabled={!isPasswordValid || !isPasswordMatch}
          onClick={handleNext}
          className={isPasswordValid && isPasswordMatch ? "!bg-[#C3304F] !text-white" : ""}
        >
          다음
        </Button> */}
          {/* 임시 버튼 */}
          <Button
            variant="gray"
            size="full"
            disabled={false} // [임시] 무조건 활성화
            onClick={() => next()} // [임시] 검사 없이 바로 다음 스텝
            className="!bg-[#C3304F] !text-white"
          >
            다음
          </Button>
      </div>
    </div>
  );
}