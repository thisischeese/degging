"use client";

import { useState, useEffect, useCallback } from "react";
import { useRouter } from "next/navigation";
import Image from "next/image";
import DatePicker, { registerLocale, DatePickerProps } from "react-datepicker";
import { ko } from "date-fns/locale/ko";

import "react-datepicker/dist/react-datepicker.css";

import Header from "@/common/components/Header";
import ReviewItem from "@/features/users/components/ReviewItem";
import { ReviewItem as OldReviewItemType } from "@/features/users/types"; // 기존 목업 컴포넌트 호환용
import { Review, MyReviewsResponse } from "@/features/reviews/types";
import { getMyReviews } from "@/features/reviews/api/reviewApi";
import backIcon from "@/assets/icons/backIcon.png";

// 한국어 로캘 등록
registerLocale("ko", ko);

/**
 * [Type Patch] react-datepicker의 공식 타입 정의가 최신 버전의 모든 Props를 포함하지 않을 수 있으므로
 * 호환성을 위해 확장 인터페이스를 정의합니다.
 */
interface ExtendedDatePickerProps extends Omit<DatePickerProps, "onChange" | "startDate" | "endDate"> {
  selectsRange: true;
  startDate: Date | undefined;
  endDate: Date | undefined;
  onChange: (update: [Date | null, Date | null], event: React.SyntheticEvent<unknown> | undefined) => void;
  fixedHeight?: boolean;
  showOtherMonths?: boolean;
}

const DatePickerComponent = DatePicker as unknown as React.ComponentType<ExtendedDatePickerProps>;

export default function MyReviewsPage() {
  const router = useRouter();

  // ─────────────────────────────────────────────────────────
  // 1. 상태 정의
  // ─────────────────────────────────────────────────────────
  const [filter, setFilter] = useState<{ startDate: Date | null; endDate: Date | null }>(() => {
    const today = new Date();
    const lastMonth = new Date();
    lastMonth.setMonth(today.getMonth() - 1);
    
    return {
      startDate: lastMonth,
      endDate: today,
    };
  });

  const [reviews, setReviews] = useState<Review[]>([]);
  const [loading, setLoading] = useState(true);
  const [page, setPage] = useState(0);
  const [isLast, setIsLast] = useState(false);

  // 날짜 포맷 (YYYY-MM-DD)
  const formatDate = (date: Date | null) => {
    if (!date) return undefined;
    const year = date.getFullYear();
    const month = String(date.getMonth() + 1).padStart(2, "0");
    const day = String(date.getDate()).padStart(2, "0");
    return `${year}-${month}-${day}`;
  };

  // ─────────────────────────────────────────────────────────
  // 2. 데이터 페칭 로직
  // ─────────────────────────────────────────────────────────
  const fetchReviews = useCallback(async (isLoadMore: boolean = false) => {
    setLoading(true);
    try {
      const currentPage = isLoadMore ? page + 1 : 0;
      const response: MyReviewsResponse = await getMyReviews(
        currentPage,
        10,
        formatDate(filter.startDate),
        formatDate(filter.endDate)
      );

      if (isLoadMore) {
        setReviews((prev) => [...prev, ...response.content]);
      } else {
        setReviews(response.content);
      }
      
      setPage(currentPage);
      setIsLast(response.last);
    } catch (error) {
      console.error("Failed to fetch reviews:", error);
    } finally {
      setLoading(false);
    }
  }, [filter.startDate, filter.endDate, page]);

  // 초기 로드
  useEffect(() => {
    fetchReviews();
  }, [fetchReviews]);

  const handleSearch = () => {
    fetchReviews(false);
  };

  // ─────────────────────────────────────────────────────────
  // 프리미엄 캘린더 커스텀 헤더
  // ─────────────────────────────────────────────────────────
  const renderCustomHeader = ({
    date,
    changeYear,
    changeMonth,
    decreaseMonth,
    increaseMonth,
    prevMonthButtonDisabled,
    nextMonthButtonDisabled,
  }: {
    date: Date;
    changeYear: (year: number) => void;
    changeMonth: (month: number) => void;
    decreaseMonth: () => void;
    increaseMonth: () => void;
    prevMonthButtonDisabled: boolean;
    nextMonthButtonDisabled: boolean;
  }) => {
    const years = Array.from({ length: 51 }, (_, i) => new Date().getFullYear() - 40 + i);
    const months = [
      "1월", "2월", "3월", "4월", "5월", "6월",
      "7월", "8월", "9월", "10월", "11월", "12월"
    ];

    return (
      <div className="flex items-center justify-center gap-6 px-3 py-2 bg-[#fcfcfc] border-b border-gray-100">
        <button
          onClick={decreaseMonth}
          disabled={prevMonthButtonDisabled}
          type="button"
          className="p-1 hover:bg-gray-200 rounded-full transition-colors disabled:opacity-20 flex items-center justify-center"
        >
          <span className="text-[16px] leading-none text-gray-400">{"<"}</span>
        </button>
        
        <div className="flex gap-1 items-center">
          <select
            value={date.getFullYear()}
            onChange={({ target: { value } }) => changeYear(Number(value))}
            className="text-[15px] font-bold border-none outline-none cursor-pointer bg-transparent text-gray-900 transition-colors"
          >
            {years.map((option) => (
              <option key={option} value={option}>
                {option}년
              </option>
            ))}
          </select>
          <select
            value={months[date.getMonth()]}
            onChange={({ target: { value } }) => changeMonth(months.indexOf(value))}
            className="text-[15px] font-bold border-none outline-none cursor-pointer bg-transparent text-gray-900 transition-colors"
          >
            {months.map((option) => (
              <option key={option} value={option}>
                {option}
              </option>
            ))}
          </select>
        </div>

        <button
          onClick={increaseMonth}
          disabled={nextMonthButtonDisabled}
          type="button"
          className="p-1 hover:bg-gray-200 rounded-full transition-colors disabled:opacity-20 flex items-center justify-center"
        >
          <span className="text-[16px] leading-none text-gray-400">{">"}</span>
        </button>
      </div>
    );
  };

  return (
    <div className="flex flex-col min-h-full bg-bg_white font-pretendard">
      {/* ── 헤더 ── */}
      <Header
        leftContent={
          <button onClick={() => router.back()} className="p-2 -ml-2 active:opacity-50 transition-opacity">
            <Image src={backIcon} alt="뒤로가기" width={24} height={24} />
          </button>
        }
        centerContent="마이 리뷰"
      />

      {/* ── 메인 콘텐츠 ── */}
      <main className="flex-1 overflow-y-auto pb-24 px-5">
        
        {/* 2. 프리미엄 검색 필터 섹션 (통합 기간 선택) */}
        <section className="bg-white rounded-[20px] border border-gray-100 shadow-sm p-4 mt-4 mb-6">
          <h2 className="text-[15px] font-bold text-gray-900 mb-4 px-1">검색 필터</h2>
          
          <div className="flex items-center gap-2">
            {/* 통합 기간 선택 영역 */}
            <div className="flex-1 relative datepicker-wrapper">
              <DatePickerComponent
                selectsRange
                startDate={filter.startDate || undefined}
                endDate={filter.endDate || undefined}
                onChange={(update) => {
                  const [start, end] = update;
                  setFilter({ startDate: start, endDate: end });
                }}
                locale="ko"
                dateFormat="yyyy.MM.dd"
                maxDate={new Date()}
                renderCustomHeader={renderCustomHeader}
                portalId="root"
                fixedHeight
                showOtherMonths
                placeholderText="조회 기간을 선택하세요"
                className="w-full h-[44px] pl-4 pr-10 rounded-xl border border-gray-200 text-[13px] text-gray-700 focus:outline-none focus:border-[#B7C26F] transition-colors bg-white cursor-pointer placeholder:text-gray-300"
              />
              <div className="absolute right-4 top-1/2 -translate-y-1/2 pointer-events-none opacity-30 text-gray-900">
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><rect x="3" y="4" width="18" height="18" rx="2" ry="2"></rect><line x1="16" y1="2" x2="16" y2="6"></line><line x1="8" y1="2" x2="8" y2="6"></line><line x1="3" y1="10" x2="21" y2="10"></line></svg>
              </div>
            </div>

            {/* 검색 버튼 */}
            <button
              onClick={handleSearch}
              className="px-5 h-[44px] bg-[#B7C26F] text-white text-[14px] font-semibold rounded-xl active:opacity-90 transition-opacity shadow-sm whitespace-nowrap ml-1"
            >
              조회
            </button>
          </div>
        </section>

        {/* 3. 리뷰 리스트 섹션 */}
        <div className="flex flex-col gap-3">
          {reviews.length > 0 ? (
            reviews.map((review) => (
              <ReviewItem 
                key={review.reviewId} 
                {...({
                  reviewId: review.reviewId, // 아이디 원본 유지
                  cafeId: 0, 
                  cafeName: review.cafeName || "카페 정보 없음",
                  cafeImageUrl: review.images[0]?.imageUrl || "/images/curation/mangoBingsu.png",
                  content: review.content,
                  createdAt: review.createdAt.split('T')[0].replaceAll('-', '.')
                } as OldReviewItemType)} 
              />
            ))
          ) : (
            <div className="flex flex-col items-center justify-center py-20 text-gray-400">
              <p className="text-[14px]">{loading ? "불러오는 중..." : "작성한 리뷰가 없습니다."}</p>
            </div>
          )}

          {/* 더보기 버튼 */}
          {!isLast && reviews.length > 0 && (
            <button 
              onClick={() => fetchReviews(true)}
              disabled={loading}
              className="mt-4 py-3 text-[14px] text-gray-500 font-medium hover:text-[#B7C26F] transition-colors"
            >
              {loading ? "불러오는 중..." : "더보기 +"}
            </button>
          )}
        </div>
      </main>

      {/* ── 프리미엄 캘린더 커스텀 스타일 (KRDS 반영 최종) ── */}
      <style jsx global>{`
        /* 캘린더 전체 팝업 커스텀 */
        .react-datepicker {
          font-family: inherit !important;
          border: 1px solid #ddd !important;
          border-radius: 20px !important;
          box-shadow: 0 15px 50px rgba(0,0,0,0.2) !important;
          overflow: hidden !important;
          background: white !important;
          padding: 0 !important;
          transform: scale(0.92);
          transform-origin: top center;
        }
        
        .react-datepicker__current-month {
          display: none !important;
        }
        
        .react-datepicker__header {
          background-color: #fcfcfc !important;
          border-bottom: 1px solid #f0f0f0 !important;
          padding: 0 !important;
        }
        
        .react-datepicker__day-names {
          display: flex !important;
          justify-content: space-between !important;
          padding: 10px 15px 0 !important;
          background-color: white !important;
        }
        
        .react-datepicker__day-name {
          color: #bbb !important;
          font-size: 11px !important;
          font-weight: 600 !important;
          width: 2.2rem !important;
          text-align: center !important;
        }
        
        .react-datepicker__month {
          margin: 0 !important;
          padding: 10px 15px 15px !important;
          background-color: white !important;
        }
        
        .react-datepicker__day {
          width: 2.2rem !important;
          line-height: 2.2rem !important;
          font-size: 13px !important;
          margin: 2px !important;
          border-radius: 50% !important;
          transition: all 0.2s ease !important;
          color: #333 !important;
          font-weight: 500 !important;
          position: relative !important;
          z-index: 1 !important;
          border-radius: 50% !important;
        }
        
        .react-datepicker__day--outside-month {
          pointer-events: none !important;
        }
        
        .react-datepicker__day:hover:not(.react-datepicker__day--outside-month) {
          background-color: #e7ecd0 !important;
          color: #B7C26F !important;
          border-radius: 50% !important;
        }
        
        .react-datepicker__day--selected,
        .react-datepicker__day--range-start,
        .react-datepicker__day--range-end,
        .react-datepicker__day--selecting-range-start,
        .react-datepicker__day--selecting-range-end,
        .react-datepicker__day--keyboard-selected,
        .react-datepicker__day--in-range.react-datepicker__day--range-end,
        .react-datepicker__day--in-range.react-datepicker__day--range-start {
          background-color: #B7C26F !important;
          color: white !important;
          font-weight: 700 !important;
          box-shadow: 0 4px 12px rgba(183, 194, 111, 0.45) !important;
          border-radius: 50% !important;
          z-index: 3 !important;
        }
        
        .react-datepicker__day--keyboard-selected:not(.react-datepicker__day--range-start):not(.react-datepicker__day--range-end) {
          background-color: transparent !important;
          color: #333 !important;
          box-shadow: none !important;
        }

        .react-datepicker__day--in-range:not(.react-datepicker__day--range-start):not(.react-datepicker__day--range-end) {
          background-color: #f2f5e5 !important;
          color: #7b8445 !important;
          border-radius: 0 !important;
          z-index: 1 !important;
        }

        .react-datepicker__day--in-selecting-range:not(.react-datepicker__day--in-range) {
          background-color: #f9fbf0 !important;
          border-radius: 0 !important;
        }

        /* [Fix] 다른 달 날짜에 선택/범위 스타일 제거 - 다른 모든 규칙 뒤에 배치해야 덮어씌워짐 */
        .react-datepicker__day--outside-month,
        .react-datepicker__day--outside-month:hover {
          color: #d0d0d0 !important;
          background-color: transparent !important;
          background: none !important;
          box-shadow: none !important;
          border: none !important;
          border-radius: 0 !important;
          font-weight: 400 !important;
          opacity: 0.45 !important;
        }

        .react-datepicker__day--today {
          color: #B7C26F !important;
          border: 1px solid #B7C26F !important;
          box-sizing: border-box !important;
        }

        /* 오늘이면서 다른 달인 경우에도 outside-month 처리 */
        .react-datepicker__day--outside-month.react-datepicker__day--today {
          color: #d0d0d0 !important;
          border: none !important;
          opacity: 0.45 !important;
        }

        .react-datepicker__navigation {
          display: none !important;
        }
        
        .react-datepicker-popper {
          z-index: 10000 !important;
        }
        .react-datepicker__triangle {
          display: none !important;
        }

        select {
          appearance: none;
          background: none;
          border: none;
          padding: 4px 10px;
          border-radius: 8px;
          transition: all 0.2s;
        }
        select:hover {
          background-color: #f2f2f2;
        }
      `}</style>
    </div>
  );
}
