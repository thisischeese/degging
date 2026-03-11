"use client";

import { useRouter } from "next/navigation";
import { ReactNode } from "react";

import Image from "next/image";
import backIcon from "@/assets/icons/backIcon.png";

interface HeaderProps {
  // 왼쪽 영역: 'back'이면 뒤로가기 아이콘, 아니면 커스텀 요소
  leftContent?: "back" | ReactNode;
  // 중앙 영역: 제목 텍스트 또는 커스텀 요소
  centerContent?: string | ReactNode;
  // 오른쪽 영역: 아이콘, 버튼, 토글 등 커스텀 요소
  rightContent?: ReactNode;

  onClickBack?: () => void;
}

export default function Header({ 
  leftContent, 
  centerContent, 
  rightContent, 
  onClickBack 
}: HeaderProps) {
  const router = useRouter();

  const handleBack = () => {
    if (onClickBack) {
      onClickBack();
    } else {
      router.back();
    }
  };

  return (
    <header className="sticky top-0 z-50 mx-auto left-0 right-0 flex h-14 w-full max-w-[375px] items-center justify-between bg-bg_white px-4 border-b border-gray-100">
      <div className="flex w-10 items-center justify-start">
        {leftContent === "back" ? (
          <button onClick={handleBack} className="p-1 active:opacity-50">
            <Image 
              src={backIcon} 
              alt="뒤로가기" 
              width={24}   
              height={24}  
              className="object-contain" 
            />
          </button>
        ) : (
          leftContent
        )}
      </div>

      {/* 2. 중앙 영역 */}
      <div className="flex flex-1 items-center justify-center overflow-hidden text-center">
        {typeof centerContent === "string" ? (
          <h1 className="truncate font-nanum_bold text-lg">{centerContent}</h1>
        ) : (
          centerContent
        )}
      </div>

      {/* 3. 오른쪽 영역 */}
s      <div className="flex w-10 items-center justify-end">
        {rightContent}
      </div>
    </header>
  );
}