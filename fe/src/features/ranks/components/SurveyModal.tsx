"use client";

import { useState, useEffect } from "react";
import { pushGtmEvent } from "@/lib/abTest";

export default function SurveyModal({
  abGroup,
  onClose,
}: {
  abGroup: 'A' | 'B' | null;
  onClose: () => void;
}) {
  const [rating1, setRating1] = useState<number>(50);
  const [favoriteFeature, setFavoriteFeature] = useState<string>("");
  const [feedback, setFeedback] = useState("");
  const [isSubmitted, setIsSubmitted] = useState(false);

  useEffect(() => {
    pushGtmEvent("survey_opened", { ab_group: abGroup });
  }, [abGroup]);

  const handleSubmit = () => {
    pushGtmEvent("survey_submitted", {
      ab_group: abGroup,
      rating_social: rating1,
      favorite_feature: favoriteFeature,
      feedback: feedback,
    });
    setIsSubmitted(true);
  };

  const handleEventClick = () => {
    pushGtmEvent("survey_event_click", { ab_group: abGroup });
    window.open("https://forms.gle/bKqRVpekLST6riP66", "_blank");
  };

  const ratingOptions = [0, 25, 50, 75, 100];

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 px-6 font-pretendard">
      <div className="w-full max-w-[320px] bg-white rounded-3xl p-5 relative shadow-lg">
        {/* 닫기 버튼 */}
        <button
          onClick={onClose}
          className="absolute top-4 right-4 p-2 text-gray-400 hover:text-gray-700 active:scale-90 transition-transform"
        >
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <line x1="18" y1="6" x2="6" y2="18"></line>
            <line x1="6" y1="6" x2="18" y2="18"></line>
          </svg>
        </button>

        {!isSubmitted ? (
          <div className="flex flex-col gap-5 mt-2">
            {/* 첫 번째 질문 */}
            <div className="flex flex-col gap-2">
              <p className="text-[14px] font-medium text-gray-800 text-center leading-relaxed">
                &quot;탐색 피드&quot;는<br />본인의 취향을 얼마나 잘 반영했나요?
              </p>
              <div className="flex justify-between px-2 pt-2 text-[12px] text-gray-500 font-medium">
                {ratingOptions.map((val) => (
                  <span key={val} className="w-8 text-center">{val}%</span>
                ))}
              </div>
              <input
                type="range"
                min="0"
                max="100"
                step="25"
                value={rating1}
                onChange={(e) => setRating1(Number(e.target.value))}
                className="w-full accent-[#B7C26F] cursor-pointer"
              />
            </div>

            {/* 두 번째 질문 (객관식) */}
            <div className="flex flex-col gap-2">
              <p className="text-[14px] font-medium text-gray-800 text-center leading-relaxed">
                &quot;가장 마음에 드는 기능&quot;을<br />선택해주세요.
              </p>
              <div className="flex flex-col gap-1.5 px-2">
                {["탐색 피드", "실시간 검색어 랭킹", "지도 필터링 기능", "오늘의 큐레이션"].map((feature) => (
                  <label key={feature} className="flex items-center gap-3 cursor-pointer py-1">
                    <input
                      type="radio"
                      name="favoriteFeature"
                      value={feature}
                      checked={favoriteFeature === feature}
                      onChange={(e) => setFavoriteFeature(e.target.value)}
                      className="w-4 h-4 appearance-none rounded-full border border-gray-300 checked:border-[#B7C26F] checked:bg-[#B7C26F] relative checked:after:content-[''] checked:after:absolute checked:after:top-[3px] checked:after:left-[3px] checked:after:w-2 checked:after:h-2 checked:after:bg-white checked:after:rounded-full cursor-pointer transition-colors"
                    />
                    <span className="text-[13px] text-gray-700">{feature}</span>
                  </label>
                ))}
              </div>
            </div>

            {/* 주관식 피드백 */}
            <div className="flex flex-col gap-2 mt-1">
              <p className="text-[13px] font-medium text-gray-700 text-center border-t border-gray-100 pt-3">
                디저트 큐레이션 Degging 대해 아쉬운 점이나 바라는 <br />
                점이 있다면 자유롭게 적어주세요.
              </p>
              <div className="relative">
                <textarea
                  value={feedback}
                  onChange={(e) => setFeedback(e.target.value)}
                  maxLength={100}
                  placeholder="의견을 남겨주세요."
                  className="w-full h-16 bg-gray-100 rounded-xl p-3 pb-6 text-[13px] text-gray-700 focus:outline-none focus:ring-1 focus:ring-[#B7C26F] resize-none"
                />
                <span className="absolute bottom-2 right-3 text-[10px] text-gray-400">
                  {feedback.length}/100
                </span>
              </div>
            </div>

            <button
              onClick={handleSubmit}
              className="mt-1 w-full max-w-[140px] mx-auto bg-[#B7C26F] text-white font-bold text-[14px] py-2.5 rounded-xl active:scale-95 transition-all shadow-sm"
            >
              제출하기
            </button>
          </div>
        ) : (
          <div className="flex flex-col items-center justify-center py-10 gap-4 mt-2">
            <h3 className="text-[18px] font-bold text-gray-900 text-center leading-tight">
              여러분의 소중한 의견이<br />반영되었습니다!<br />감사합니다.
            </h3>
            <p className="text-[12px] text-gray-500 mt-2 mb-4">
              번호 남기고 기프티콘 당첨 기회 잡자~!
            </p>
            <button
              onClick={handleEventClick}
              className="w-full max-w-[160px] bg-[#B7C26F] text-white font-bold text-[14px] py-3 rounded-xl active:scale-95 transition-all shadow-sm"
            >
              이벤트 응모하기
            </button>
          </div>
        )}
      </div>
    </div>
  );
}
