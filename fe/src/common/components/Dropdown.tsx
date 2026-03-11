'use client';

import React, { useState, useRef, useEffect } from 'react';
import { ChevronDown } from 'lucide-react';

export interface DropdownOption {
    value: string;
    label: string;
}

export interface DropdownProps {
    options: DropdownOption[];
    value: string;
    onChange: (value: string) => void;
    className?: string;
}

export const Dropdown = ({ options, value, onChange, className = '' }: DropdownProps) => {
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

            {isOpen && (
                <div className="absolute top-full mt-1.5 left-0 w-max min-w-[120px] bg-white border border-gray-200 rounded-[12px] shadow-[0_4px_16px_rgba(0,0,0,0.08)] z-50 overflow-hidden flex flex-col">
                    {options.map((option, index) => (
                        <button
                            key={option.value}
                            type="button"
                            onClick={() => {
                                onChange(option.value);
                                setIsOpen(false);
                            }}
                            className={`w-full flex items-center px-4 py-3 text-[14px] text-gray-800 bg-white hover:bg-gray-50 active:bg-gray-100 transition-colors ${index !== options.length - 1 ? 'border-b border-gray-100' : ''
                                }`}
                        >
                            {option.label}
                        </button>
                    ))}
                </div>
            )}
        </div>
    );
};
