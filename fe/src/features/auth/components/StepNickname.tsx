"use client";

import { useState } from "react";
import Image from "next/image";
import { Input } from "@/common/components/Input";
import Button from "@/common/components/Button";
import { SignupStepProps } from "../types";

export default function StepNickname({ next, updateData }: SignupStepProps) {
  const [nickname, setNickname] = useState("");
  const [birthDate, setBirthDate] = useState("");
  const [gender, setGender] = useState<"MALE" | "FEMALE" | null>(null);
  const [isCheck, setIsCheck] = useState(false);
  const [nicknameError, setNicknameError] = useState("");

  // 닉네임 중복 검사 로직
  const handleCheckNickname = () => {
    if (nickname.length < 2) {
      setNicknameError("닉네임은 2자 이상이어야 합니다.");
      return;
    }
    // [임시] admin일 때만 중복 에러 테스트
    if (nickname === "admin") {
      setNicknameError("이미 사용 중인 닉네임입니다.");
      setIsCheck(false);
    } else {
      setNicknameError("");
      setIsCheck(true);
      alert("사용 가능한 닉네임입니다.");
    }
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

  const handleNext = () => {
    // 모든 조건 충족 시 다음 단계
    if (isCheck && birthDate.length === 10 && gender) {
      // API 명세서에 맞춰 birthDate로 전달 (YYYY-MM-DD 형식으로 변환이 필요할 수 있음)
      // 현재는 UI용 포맷(YYYY.MM.DD)이므로 서버 전송 시에는 .을 -로 바꿉니다.
      const formattedBirthDate = birthDate.replace(/\./g, "-");
      updateData({ nickname, birthDate: formattedBirthDate, gender });
      next();
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
            placeholder="2~10자 이내의 한글, 영문"
            value={nickname}
            onChange={(e) => { 
              setNickname(e.target.value); 
              setIsCheck(false); // 수정 시 중복검사 다시 하도록 초기화
              setNicknameError("");
            }}
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