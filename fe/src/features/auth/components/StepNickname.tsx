"use client";

import { useState } from "react";
import Image from "next/image";
import { Input } from "@/common/components/Input";
import Button from "@/common/components/Button";
import { SignupStepProps } from "../types";

export default function StepNickname({ next, updateData, formData }: SignupStepProps) {
  const [nickname, setNickname] = useState("");
  const [birthDate, setBirthDate] = useState("");
  const [gender, setGender] = useState<"MALE" | "FEMALE" | null>(null);
  const [isCheck, setIsCheck] = useState(false);
  const [nicknameError, setNicknameError] = useState("");
  const [nicknameSuccess, setNicknameSuccess] = useState(""); // 추가: 성공 메시지용 상태

  // 닉네임 유효성 검사 (실시간 에러 메시지용)
  const validateNickname = (value: string) => {
    if (value.length === 0) {
      setNicknameError("");
      setNicknameSuccess("");
      return false;
    }
    
    // 1. 문자 규칙 검사: 영어, 숫자, 완성된 한글만 허용 (자음, 모음, 공백, 특수문자 금지)
    const nicknameRegex = /^[a-zA-Z0-9가-힣]+$/;
    if (!nicknameRegex.test(value)) {
      setNicknameError("공백, 특수문자, 자음/모음은 사용할 수 없습니다.");
      setNicknameSuccess("");
      return false;
    }

    // 2. 글자 수 검사
    if (value.length < 2 || value.length > 10) {
      setNicknameError("닉네임은 2~10자 사이여야 합니다.");
      setNicknameSuccess("");
      return false;
    }

    setNicknameError("");
    setNicknameSuccess("");
    return true;
  };

  // 닉네임 중복 검사 로직
  const handleCheckNickname = () => {
    if (!validateNickname(nickname)) return;

    // [임시] admin일 때만 중복 에러 테스트
    if (nickname === "admin") {
      setNicknameError("이미 사용 중인 닉네임입니다.");
      setNicknameSuccess("");
      setIsCheck(false);
    } else {
      setNicknameError("");
      setNicknameSuccess("사용 가능한 닉네임입니다."); // 성공 시 인라인 텍스트 설정
      setIsCheck(true);
    }
  };

  // 닉네임 입력 핸들러 (IME 이슈 해결을 위해 실시간 필터링 대신 유효성 검사만 수행)
  const handleNicknameChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const value = e.target.value;
    setNickname(value);
    setIsCheck(false);
    validateNickname(value);
  };

  // 생년월일 포맷팅 (YYYY.MM.DD)
  const handleBirthChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const value = e.target.value.replace(/[^0-9]/g, "");
    let formattedValue = "";
    
    if (value.length <= 4) formattedValue = value;
    else if (value.length <= 6) formattedValue = `${value.slice(0, 4)}.${value.slice(4)}`;
    else formattedValue = `${value.slice(0, 4)}.${value.slice(4, 6)}.${value.slice(6, 8)}`;

    if (value.length <= 8) setBirthDate(formattedValue);
  };

  // 생년월일 유효성 검사 로직
  const isValidDate = (dateString: string) => {
    if (dateString.length !== 10) return false;
    
    const year = parseInt(dateString.substring(0, 4), 10);
    const month = parseInt(dateString.substring(5, 7), 10);
    const day = parseInt(dateString.substring(8, 10), 10);

    // 1. 월 검사 (1~12)
    if (month < 1 || month > 12) return false;

    // 2. 일 검사 (1~31) 및 해당 월의 마지막 날짜(윤년 포함) 계산
    const lastDayOfMonth = new Date(year, month, 0).getDate();
    if (day < 1 || day > lastDayOfMonth) return false;

    // 3. 연도 검사 (미래 날짜, 너무 옛날 방지)
    const currentYear = new Date().getFullYear();
    if (year < 1900 || year > currentYear) return false;

    return true;
  };

  const birthDateError = 
    birthDate.length === 10 && !isValidDate(birthDate) ? "유효한 날짜를 입력해주세요." : "";

  const handleNext = () => {
    // 모든 조건 충족 시 다음 단계
    if (isCheck && birthDate.length === 10 && isValidDate(birthDate) && gender) {
      // 마침표(.)를 하이픈(-)으로 변환하여 백엔드 표준에 맞춥니다.
      const formattedBirthDate = birthDate.replace(/\./g, "-"); 
      const stepData = { nickname, birthDate: formattedBirthDate, gender };
      updateData(stepData);
      next(stepData);
    }
  };

  return (
    <div className="flex flex-col h-full">
      {/* 상단 Step 표시 - 세 번째 단계 활성화 */}
      <div className="flex justify-center gap-2 mt-4 mb-10">
        <div className="w-1.5 h-1.5 rounded-full bg-gray-300" />
        <div className="w-1.5 h-1.5 rounded-full bg-gray-300" />
        <div className="w-1.5 h-1.5 rounded-full bg-black" />
      </div>

      {/* 로고 영역 (이전 단계와 동일) */}
      <div className="flex flex-col items-center mb-12">
        <Image src="/images/common/logo.png" alt="Logo" width={120} height={120} className="object-contain" />
      </div>

      {/* 입력 폼 영역 */}
      <div className="flex-1">
        {/* 닉네임 입력 (이메일 인증 버튼과 동일한 구조 적용) */}
        <div className="h-[94px]">
          <Input
            label="닉네임"
            placeholder="한글/영어/숫자 2~10자"
            value={nickname}
            onChange={handleNicknameChange}
            error={nicknameError}
            rightElement={
              <Button 
                variant="gray" 
                size="sm" 
                onClick={handleCheckNickname}
                disabled={!nickname}
                className="w-[84px]"
              >
                중복 확인
              </Button>
            }
          />
          {/* 에러가 없고 성공 메시지가 있을 때 파란색으로 표시 */}
          {!nicknameError && nicknameSuccess && (
            <p className="text-xs font-pretendard text-blue-500 px-1 mt-0.5 animate-in slide-in-from-top-1 fade-in duration-200">
              {nicknameSuccess}
            </p>
          )}
        </div>

        {/* 생년월일 & 성별 가로 배치 (mt-4 간격 유지) */}
        <div className="flex gap-4 mt-4 h-[94px]">
          {/* 생년월일 */}
          <div className="flex-[1.5]">
            <Input
              label="생년월일"
              placeholder="YYYY.MM.DD"
              value={birthDate}
              onChange={handleBirthChange}
              inputMode="numeric"
              error={birthDateError}
            />
          </div>
          
          {/* 성별 선택 */}
          <div className="flex-1 flex flex-col gap-2">
            <label className="text-sm font-pretendard text-gray-800 px-1 tracking-tight">성별</label>
            <div className="flex h-[48px] border border-gray-300 rounded-xl overflow-hidden">
              <button
                type="button"
                onClick={() => setGender("MALE")}
                className={`flex-1 text-sm transition-colors ${gender === "MALE" ? "bg-[#C3304F] text-white font-bold" : "bg-white text-gray-500"}`}
              >
                남
              </button>
              <div className="w-px bg-gray-300 my-2" />
              <button
                type="button"
                onClick={() => setGender("FEMALE")}
                className={`flex-1 text-sm transition-colors ${gender === "FEMALE" ? "bg-[#C3304F] text-white font-bold" : "bg-white text-gray-500"}`}
              >
                여
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* 하단 다음 버튼 (StepTrend와 동일한 mt-2 적용) */}
      <div className="pb-4 mt-2">
        <div className="min-h-[24px] mb-2 text-center">
          {/* 에러메시지용 공간 */}
        </div>
        <Button
          variant="gray"
          size="full"
          disabled={!isCheck || birthDate.length !== 10 || !gender}
          onClick={handleNext}
          className={isCheck && birthDate.length === 10 && gender ? "bg-[#C3304F]! text-white!" : ""}
        >
          다음 단계로
        </Button>
      </div>
    </div>
  );
}