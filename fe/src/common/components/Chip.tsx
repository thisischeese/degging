import React from 'react';
import { Check } from 'lucide-react';

export interface ChipProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  label: string;
  variant: 'onboarding' | 'map';
  isActive: boolean;
}

export const Chip = ({
  label,
  variant,
  isActive,
  onClick,
  className = '',
  ...props
}: ChipProps) => {
  // 공통 스타일: 글꼴, 둥근 모서리, 유동적 너비, 전환 효과
  const baseStyles = 'w-fit rounded-full flex items-center justify-center transition-colors duration-200 font-pretendard border px-4 py-2 text-sm font-medium gap-1.5 cursor-pointer';

  let variantStyles = '';

  // 변종 1 & 2 스타일 분기 처기
  if (variant === 'onboarding') {
    if (isActive) {
      // 투명도 15% 적용 (/15)
      variantStyles = 'border-[#C3304F] bg-[#C3304F]/15 text-[#C3304F]';
    } else {
      // 연한 회색 외곽선, 투명 배경, 회색 텍스트
      variantStyles = 'border-gray-200 bg-transparent text-gray-500 hover:bg-gray-50/50';
    }
  } else if (variant === 'map') {
    if (isActive) {
      // 투명도 15% 적용 (/15)
      variantStyles = 'border-[#AC7F5E] bg-[#AC7F5E]/15 text-[#AC7F5E]';
    } else {
      // 흰색 배경, 회색 외곽선, 짙은 회색 텍스트
      variantStyles = 'border-gray-300 bg-white text-gray-700 hover:bg-gray-50';
    }
  }

  return (
    <button
      type="button"
      onClick={onClick}
      className={`${baseStyles} ${variantStyles} ${className}`}
      {...props}
    >
      {variant === 'onboarding' && isActive && (
        <Check size={16} strokeWidth={2.5} />
      )}
      {label}
    </button>
  );
};
