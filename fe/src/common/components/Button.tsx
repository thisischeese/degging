'use client';

import { ReactNode } from 'react';

interface ButtonProps {
  children: React.ReactNode;
  onClick?: () => void;
  variant?: 'primary' | 'gray' | 'kakao' | 'black' | 'outline';
  size?: 'full' | 'md' | 'sm';
  disabled?: boolean;
  type?: 'button' | 'submit';
  className?: string; 
}

export default function Button({
  children,
  onClick,
  variant = 'primary',
  size = 'md',
  disabled = false,
  type = 'button',
  className = '',
}: ButtonProps) {
  
  // 1. 색상(Variant) 스타일 정의
  const variantStyles = {
    primary: 'bg-primary_btn_red text-white disabled:bg-primary_btn_gray',
    gray: 'bg-primary_btn_gray text-white',
    kakao: 'bg-[#FEE500] text-[#3c1e1e]',
    black: 'bg-black text-white',
    outline: 'bg-white border border-gray-200 text-gray-700', // 스크랩용
  };

  // 2. 크기(Size) 스타일 정의
  const sizeStyles = {
    full: 'w-full h-[42px] rounded-xl text-sm font-semibold tracking-tight', // Auth 긴 버튼
    md: 'px-8 h-[40px] rounded-full text-sm font-medium',   // 모달용
    sm: 'px-3 h-[32px] rounded-md text-xs font-medium',    // 중복검사/인증용 (회색 고정용)
  };

  return (
    <button
      type={type}
      onClick={onClick}
      disabled={disabled}
      className={`flex items-center justify-center transition-all active:scale-[0.98] ${variantStyles[variant]} ${sizeStyles[size]}`}
    >
      {children}
    </button>
  );
}