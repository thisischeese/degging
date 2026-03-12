import React, { InputHTMLAttributes, TextareaHTMLAttributes, useId } from 'react';

interface BaseProps {
    /** 입력창 상단에 표시될 라벨 */
    label?: string;
    /** 에러 상황 시 테두리를 붉게 만들고 하단에 표시할 메시지 */
    error?: string;
    /** 입력창 우측에 배치할 요소 (버튼, 아이콘 등) - Input 모드에서만 지원 */
    rightElement?: React.ReactNode;
    /** 최상위 컨테이너 요소에 추가할 클래스네임 */
    containerClassName?: string;
}

/** 기본 Input(한 줄 입력) 모드일 때의 Props */
export type InputProps = BaseProps &
    Omit<InputHTMLAttributes<HTMLInputElement>, 'className'> & {
        /** 한 줄 입력 모드 (기본값) */
        isMultiline?: false;
        /** input 요소에 직접 적용할 커스텀 스타일 클래스 */
        className?: string;
    };

/** Textarea(여러 줄 입력) 모드일 때의 Props */
export type TextareaProps = BaseProps &
    Omit<TextareaHTMLAttributes<HTMLTextAreaElement>, 'className'> & {
        /** true일 경우 textarea로 렌더링 */
        isMultiline: true;
        /** textarea 요소에 직접 적용할 커스텀 스타일 클래스 */
        className?: string;
    };

/** * 최종 컴포넌트 Props 타입 
 * isMultiline 값에 따라 Input 또는 Textarea의 고유 속성을 선택적으로 지원합니다.
 */
export type InputComponentProps = InputProps | TextareaProps;


/**
 * ## Degging 공통 TextField 컴포넌트
 * * 일반 입력창(Input)과 리뷰 작성 등을 위한 여러 줄 입력창(Textarea)을 모두 지원합니다.
 * 모든 텍스트는 `font-pretendard`가 적용되어 있습니다.
 * * @example
 * // 1. 기본 입력창
 * <Input label="이메일" placeholder="이메일을 입력하세요" />
 * * @example
 * // 2. 에러 상태 및 버튼 포함
 * <Input 
 * label="인증번호" 
 * error="번호가 일치하지 않습니다" 
 * rightElement={<button>확인</button>} 
 * />
 * * @example
 * // 3. 여러 줄 입력 (Textarea)
 * <Input isMultiline label="리뷰" rows={5} />
 */
export const Input = React.forwardRef<HTMLInputElement | HTMLTextAreaElement, InputComponentProps>(
    (props, ref) => {
        // 내부적으로 고유 id 부여 (label과 연결용)
        const id = useId();

        // isMultiline에 따른 Props 분리
        const {
            label,
            error,
            rightElement,
            containerClassName,
            isMultiline,
            className,
            ...rest
        } = props as InputComponentProps;

        // 공통 스타일 (font-pretendard, 테두리, 포커스링, 배경색 등)
        // Tailwind v4 적용: primary_btn_red, primary_btn_gray, bg_white 사용
        const baseStyle = [
            'w-full px-4 py-3 rounded-xl border text-base outline-none transition-all duration-200',
            'font-pretendard placeholder:text-gray-400 bg-bg_white',
            error
                ? 'border-primary_btn_red text-primary_btn_red focus:border-primary_btn_red focus:ring-1 focus:ring-primary_btn_red'
                : 'border-primary_btn_gray text-gray-800 focus:border-gray-500 focus:ring-1 focus:ring-gray-500',
        ].join(' ');

        return (
            <div className={`flex flex-col w-full gap-2 ${containerClassName || ''}`}>
                {/* 1. 상단 라벨 (font-nanum_bold 적용) */}
                {label && (
                    <label htmlFor={id} className="text-sm font-pretendard text-gray-800 px-1 tracking-tight">
                        {label}
                    </label>
                )}

                {/* 2. 입력 영역 */}
                <div className="relative flex items-center w-full">
                    {isMultiline ? (
                        <textarea
                            id={id}
                            ref={ref as React.Ref<HTMLTextAreaElement>}
                            className={`${baseStyle} resize-none min-h-[120px] ${className || ''}`}
                            {...(rest as Omit<TextareaHTMLAttributes<HTMLTextAreaElement>, 'className'>)}
                        />
                    ) : (
                        <input
                            id={id}
                            ref={ref as React.Ref<HTMLInputElement>}
                            // 우측 요소가 있을 경우 패딩을 추가 확보 (예: pr-20)
                            className={`${baseStyle} ${rightElement ? 'pr-[88px]' : ''} ${className || ''}`}
                            {...(rest as Omit<InputHTMLAttributes<HTMLInputElement>, 'className'>)}
                        />
                    )}

                    {/* 3. 우측 버튼/아이콘 영역 (Input 타입일 때만) */}
                    {rightElement && !isMultiline && (
                        <div className="absolute right-2 flex items-center justify-center p-1">
                            {rightElement}
                        </div>
                    )}
                </div>

                {/* 4. 에러 메시지 */}
                {error && (
                    <p className="text-xs font-pretendard text-primary_btn_red px-1 mt-0.5 animate-in slide-in-from-top-1 fade-in duration-200">
                        {error}
                    </p>
                )}
            </div>
        );
    }
);

Input.displayName = 'Input';
