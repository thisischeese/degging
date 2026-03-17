'use client';

import React, { useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Info, X } from 'lucide-react';

interface PopUpProps {
  message: string;
  isVisible: boolean;
  onClose: () => void;
  /** 자동으로 닫힐 시간 (ms), 기본값 3000ms */
  duration?: number;
}

export default function PopUp({ message, isVisible, onClose, duration = 3000 }: PopUpProps) {
  useEffect(() => {
    if (isVisible) {
      const timer = setTimeout(() => {
        onClose();
      }, duration);
      return () => clearTimeout(timer);
    }
  }, [isVisible, duration, onClose]);

  return (
    <AnimatePresence>
      {isVisible && (
        <motion.div
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          exit={{ opacity: 0, y: -20 }}
          transition={{ duration: 0.3, ease: 'easeOut' }}
          className="fixed top-20 left-0 right-0 z-[100] flex justify-center px-4 pointer-events-none"
        >
          <div className="bg-white border-[0.2px] border-[#2A2A2A] rounded-xl shadow-[0_8px_30px_rgb(0,0,0,0.08)] px-4 py-3.5 w-full max-w-[343px] flex items-center justify-between pointer-events-auto">
            <div className="flex items-center gap-3">
              <div className="flex items-center justify-center shrink-0">
                <Info className="w-6 h-6 text-gray-900" strokeWidth={1.5} />
              </div>
              <span className="text-[14px] text-gray-900 font-pretendard font-medium tracking-tight">
                {message}
              </span>
            </div>
            <button
              onClick={onClose}
              className="w-8 h-8 flex items-center justify-center shrink-0 -mr-2"
            >
              <X className="w-5 h-5 text-gray-900" strokeWidth={1.5} />
            </button>
          </div>
        </motion.div>
      )}
    </AnimatePresence>
  );
}
