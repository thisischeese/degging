"use client"; // 모달은 사용자 인터랙션(클릭 등)을 처리해야 하므로 반드시 클라이언트 컴포넌트여야 합니다.

import React, { useEffect, useState } from "react";
import { createPortal } from "react-dom";

// 모달 컴포넌트가 받을 수 있는 옵션(Props)들을 정의합니다.
// Button.tsx에서 variant, size 등을 받았던 것과 같은 원리입니다!
export interface ModalProps {
  /** 모달이 화면에 보여질지 말지 결정하는 상태 (true면 보이고, false면 숨김) */
  isOpen: boolean;
  /** 모달을 닫을 때 실행할 함수 (보통 '취소' 버튼이나 어두운 바탕을 눌렀을 때 발동) */
  onClose: () => void;
  /** 바탕(어두운 화면)을 클릭해도 모달이 안 닫히게 막고 싶을 때 true로 설정 */
  disableBackdropClick?: boolean;
  /** 모달의 가로 크기 결정 (sm: 기본 작은 팝업, lg: 프로필 등 큰 팝업) */
  size?: 'sm' | 'lg';
  /** 모달 안쪽에 들어갈 내용 (모달창 안에 넣을 글씨, 이미지, 버튼 컴포넌트 등) */
  children: React.ReactNode;
}

export default function Modal({
  isOpen,
  onClose,
  disableBackdropClick = false,
  size = 'sm',
  children,
}: ModalProps) {
  // 모달이 브라우저(document)에 마운트(그려졌는지) 확인하는 상태입니다.
  // Next.js는 처음에 서버에서 뼈대(HTML)를 먼저 만들기 때문에, 브라우저에만 있는 'document'에 
  // 바로 접근하려고 하면 에러가 납니다. 그래서 화면이 확실히 켜진 뒤에 모달을 띄우기 위한 장치입니다.
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    // 1. 컴포넌트가 처음 화면에 그려질 때 딱 한 번만 mounted 상태를 true로 변경합니다.
    // eslint-disable-next-line
    setMounted(true); 
  }, []);

  useEffect(() => {
    // 2. 모달이 열려있을 때(isOpen === true) 스마트폰 뒤쪽 배경이 같이 스크롤되는 것을 막아줍니다!
    // 진짜 앱처럼 뒤에는 가만히 멈춰있게 해줍니다.
    if (isOpen) {
      document.body.style.overflow = "hidden";
    } else {
      document.body.style.overflow = "unset";
    }

    // 3. 모달 컴포넌트가 꺼지거나 파괴될 때 스크롤 잠금을 원래대로 풀어주는 '청소기' 역할입니다.
    return () => {
      document.body.style.overflow = "unset";
    };
  }, [isOpen]); // isOpen 상태가 바뀔 때마다 이 useEffect 안의 로직을 다시 실행합니다.

  // isOpen이 false이거나, 아직 브라우저에 안 그려졌다면 아무것도 렌더링하지 않습니다(숨깁니다).
  if (!isOpen || !mounted) return null;

  // 어두운 배경(Backdrop)을 클릭했을 때 모달을 닫는 동작입니다.
  const handleBackdropClick = () => {
    if (!disableBackdropClick) {
      onClose();
    }
  };

  // 피그마 디자인을 반영하여 size prop에 따라 모달 박스의 최대 가로 길이를 다르게 지정합니다.
  const sizeStyles = {
    sm: "max-w-[320px]", // 카테고리 삭제, 비밀번호 전송 등 내용이 적은 작은 팝업
    lg: "max-w-[350px]", // 프로필 정보 변경, 카테고리 수정 등 입력란이 많은 큰 팝업
  };

  // 모달 전체 UI 구성
  // font-pretendard 클래스를 최상단에 줘서 이 모달 안의 모든 글씨는 프리텐다드 폰트가 적용되게 묶어줍니다.
  const modalContent = (
    <div 
      className="fixed inset-0 z-100 flex items-center justify-center bg-black/40 px-4 font-pretendard transition-opacity"
      onClick={handleBackdropClick} // 어두운 배경을 누르면 닫힘
    >
      {/* 
        실제 하얀색 모달 박스 영역 
        부모의 onClick 이벤트(닫기 동작)가 자식인 이 하얀 박스까지 전달되지 않도록 방패막(e.stopPropagation)을 쳐줍니다.
        이게 없으면 하얀 박스 안에서 글씨만 클릭해도 모달이 꺼져버립니다!
      */}
      <div 
        className={`w-full bg-white rounded-[24px] p-6 shadow-xl relative ${sizeStyles[size]}`}
        onClick={(e) => e.stopPropagation()} 
      >
        {children}
      </div>
    </div>
  );

  // createPortal: Next.js(React) 구조상 모달 컴포넌트를 어디서 쓰든 간에,
  // 실제 HTML 구조에서는 <body> 태그 바로 아래에 독립적으로 가장 높이 둥둥 떠있게(제일 위로) 뽑아내 줍니다.
  // 이렇게 해야 다른 레이아웃 요소들에 파묻히지 않고 완벽하게 최상단에 뜨게 됩니다!
  return createPortal(modalContent, document.body);
}
