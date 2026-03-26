'use client';

import React, { useState, useRef, useEffect } from 'react';
import { ChevronDown } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';

export interface DropdownOption {
    value: string;
    label: string;
}

export interface DropdownProps {
    options: DropdownOption[];
    value: string;
    onChange: (value: string) => void;
    className?: string;
    triggerNode?: React.ReactNode;
}

export const Dropdown = ({ options, value, onChange, className = '', triggerNode }: DropdownProps) => {
    const [isOpen, setIsOpen] = useState(false);
    const dropdownRef = useRef<HTMLDivElement>(null);

    const selectedOption = options.find((opt) => opt.value === value) || options[0];

    useEffect(() => {
        const handleClickOutside = (event: MouseEvent) => {
            if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
                setIsOpen(false);
            }
        };
        document.addEventListener('mousedown', handleClickOutside);
        return () => document.removeEventListener('mousedown', handleClickOutside);
    }, []);

    return (
        <div className={`relative ${className}`} ref={dropdownRef}>
            {triggerNode ? (
                <div onClick={() => setIsOpen(!isOpen)} className="cursor-pointer">
                    {triggerNode}
                </div>
            ) : (
                /* 기존 코드 주석 (너비 가변 문제 해결 위해 수정)
                <button
                    type="button"
                    onClick={() => setIsOpen(!isOpen)}
                    className="flex items-center gap-1.5 px-3 py-1.5 bg-white border border-gray-200 rounded-[8px] text-[14px] font-medium text-gray-900 active:bg-gray-50 transition-colors"
                >
                    {selectedOption.label}
                    <ChevronDown
                        className={`w-4 h-4 text-gray-900 transition-transform ${isOpen ? 'rotate-180' : ''}`}
                        strokeWidth={2.5}
                    />
                </button>
                */
                <button
                    type="button"
                    onClick={() => setIsOpen(!isOpen)}
                    // [수정] 내부 텍스트 길이에 관계없이 레이아웃이 유지되도록 최소 너비와 justify-between 선언
                    className="flex items-center justify-between w-full min-w-[110px] gap-1.5 px-3 py-1.5 bg-white border border-gray-200 rounded-[8px] text-[14px] font-medium text-gray-900 active:bg-gray-50 transition-colors shrink-0"
                >
                    <span className="text-left flex-1">{selectedOption.label}</span>
                    <ChevronDown
                        className={`w-4 h-4 text-gray-900 transition-transform ${isOpen ? 'rotate-180' : ''} shrink-0`}
                        strokeWidth={2.5}
                    />
                </button>
            )}

            <AnimatePresence>
                {isOpen && (
                    <motion.div
                        initial={{ opacity: 0, y: -10 }}
                        animate={{ opacity: 1, y: 0 }}
                        exit={{ opacity: 0, y: -10 }}
                        transition={{ duration: 0.2 }}
                        className="absolute top-full mt-1.5 right-0 w-max min-w-[120px] bg-white border border-gray-200 rounded-[12px] shadow-[0_4px_16px_rgba(0,0,0,0.08)] z-50 overflow-hidden flex flex-col"
                    >
                        {options.map((option, index) => (
                            <button
                                key={option.value}
                                type="button"
                                onClick={() => {
                                    onChange(option.value);
                                    setIsOpen(false);
                                }}
                                // [delete일 때 빨간 글씨 되도록 수정, 글 중앙 정렬]
                                className={`w-full flex items-center justify-center px-4 py-3 text-[16px] transition-colors hover:bg-gray-50 active:bg-gray-100 ${index !== options.length - 1 ? 'border-b border-gray-100' : ''
                                    } ${option.value === 'delete' ? 'text-[#C3304F]' : 'text-gray-800'
                                    }`}
                            >
                                {option.label}
                            </button>
                        ))}
                    </motion.div>
                )}
            </AnimatePresence>
        </div>
    );
};
