"use client";

import { useState } from "react";
import Image from "next/image";
import { useRouter } from "next/navigation";
import { Input } from "@/common/components/Input";
import Button from "@/common/components/Button";
import Modal from "@/common/components/Modal";

export default function FindPasswordPage() {
  const [email, setEmail] = useState("");
  const [isSent, setIsSent] = useState(false);
  const router = useRouter();

  const handleSend = () => {
    // API 연결 지점: 입력한 이메일로 임시 비밀번호 발송 요청
    console.log("임시 비밀번호 전송 요청:", email);
    setIsSent(true);
  };

  return (
    <div className="flex flex-col h-full px-6 bg-bg_white relative font-pretendard">
      {/* 1. 상단 로고: 로그인 페이지와 완벽하게 동일한 위치와 크기 */}
      <div className="mt-[56px] flex flex-col items-center mb-20 shrink-0">
        <Image
          src="/images/common/logo.png"
          alt="Degging Logo"
          width={120}   // 로그인 페이지에서 키운 사이즈와 동일하게 설정
          height={120}
          className="object-contain"
        />
      </div>

      {/* 2. 콘텐츠 영역 */}
      <div className="flex flex-col text-center mb-10">
        <h2 className="text-[26px] font-bold text-gray-900 mb-4">비밀번호 찾기</h2>
        <p className="text-sm text-gray-500 leading-relaxed tracking-tight px-2">
          가입하신 이메일을 입력해 주세요.<br />
          입력하신 이메일로 임시 비밀번호를 보내드립니다.
        </p>
      </div>

      {/* 3. 입력 폼: h-[94px] 구조 유지 */}
      <div className="mb-4">
        <div className="h-[94px]">
          <Input
            label="이메일"
            placeholder="이메일을 입력하세요"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
          />
        </div>
      </div>

      {/* 4. 전송 버튼 */}
      <div className="pb-8">
        <Button
          variant={email.includes("@") ? "primary" : "gray"}
          size="full"
          disabled={!email.includes("@")}
          onClick={handleSend}
          className={email.includes("@") ? "!bg-primary_btn_red !text-white" : ""}
        >
          전송
        </Button>
      </div>

      {/* 5. 임시 비밀번호 전송 완료 팝업 (모달) */}
      <Modal
        isOpen={isSent}
        onClose={() => setIsSent(false)}
        size="sm"
      >
        <div className="flex flex-col items-center">
          <span className="text-4xl mb-4">🎉</span>
          <p className="text-[15px] font-medium text-gray-800 text-center mb-8 leading-snug">
            이메일로 임시 비밀번호가 전송되었습니다!
          </p>
          <Button
            variant="primary"
            size="full"
            className="!rounded-xl"
            onClick={() => {
              setIsSent(false);
              router.push("/login");
            }}
          >
            확인
          </Button>
        </div>
      </Modal>
    </div>
  );
}