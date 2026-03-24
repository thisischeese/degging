"use client";

import { useState } from "react";
import Image from "next/image";
import Link from "next/link";
import { Input } from "@/common/components/Input";
import Button from "@/common/components/Button";
import { postLogin } from "@/features/auth/api/loginApi";

export default function LoginPage() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");

  const handleLogin = async () => {
    try {
      // 1. API 호출 (이제 .data까지 언래핑된 데이터를 바로 받습니다)
      const loginData = await postLogin({ email, password });

      // 2. 성공 시
      console.log("로그인 성공!", loginData);
      
      sessionStorage.setItem("access_token", loginData.accessToken);
      sessionStorage.setItem("refresh_token", loginData.refreshToken);

      window.location.href = "/"; // 메인으로 이동
    } catch (error) {
      console.error("로그인 실패:", error);
      alert("이메일 또는 비밀번호가 올바르지 않습니다.");
    }
  };

  return (
    <div className="flex flex-1 min-h-0 flex-col overflow-y-auto no-scrollbar px-6 py-12 font-pretendard">
      {/* 상단 로고 */}
      <div className="flex flex-col items-center mb-10">
        <Image src="/images/common/logo.png" alt="Logo" width={120} height={120} className="object-contain" />
      </div>

      {/* 소셜 로그인 섹션 (Button 컴포넌트 활용) */}
      <div className="flex flex-col gap-3 mb-8">
        <Button variant="kakao" size="full" onClick={() => alert("준비 중")}>
          카카오로 계속하기
        </Button>
        <Button variant="black" size="full" onClick={() => alert("준비 중")}>
          구글로 계속하기
        </Button>
      </div>

      {/* 구분선 */}
      <div className="flex items-center gap-4 mb-8">
        <div className="flex-1 h-[1px] bg-gray-100" />
        <span className="text-[11px] text-gray-400">또는</span>
        <div className="flex-1 h-[1px] bg-gray-100" />
      </div>

      {/* 입력 폼 섹션 (공통 Input 활용) */}
      <div className="flex flex-col gap-4 mb-4">
        <Input
          label="이메일"
          placeholder="이메일을 입력하세요"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
        />
        <Input
          label="비밀번호"
          type="password"
          placeholder="비밀번호를 입력하세요"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
        />
      </div>

      {/* 로그인 버튼 (입력 여부에 따라 primary 색상 활성화) */}
      <Button
        variant={email && password ? "primary" : "gray"}
        size="full"
        disabled={!email || !password}
        onClick={handleLogin}
        className="shrink-0"
      >
        로그인
      </Button>

      {/* 하단 보조 링크 */}
      <div className="mt-8 text-center">
        <Link
          href="/password"
          className="text-xs text-gray-400 underline underline-offset-4 decoration-gray-200"
        >
          비밀번호를 잊으셨나요?
        </Link>
      </div>
    </div>
  );
}