'use client';

import React, { useEffect, useState, use } from 'react';
import { useRouter } from 'next/navigation';
import Image from 'next/image';
import { motion, AnimatePresence } from 'framer-motion';
import { X, Check, Info } from 'lucide-react';
import Modal from '@/common/components/Modal';
import Button from '@/common/components/Button';
import { Input } from '@/common/components/Input';
import { StarColor } from '@/features/scraps/types';

interface CafeDetail {
  id: string;
  name: string;
  description: string;
  rating: number;
  reviewCount: number;
  businessHours: string;
  address: string;
  phone: string;
  imageUrls: string[];
  menuList: { name: string; price: string; imageUrl: string }[];
}

// 스크랩 카테고리 (오버레이용)
interface ScrapCategoryOption {
  categoryId: number;
  name: string;
}

const MOCK_SCRAP_CATEGORIES: ScrapCategoryOption[] = [
  { categoryId: 0, name: "기본 스크랩" },
  { categoryId: 1, name: "연남 분좋카 투어" },
  { categoryId: 2, name: "내 사랑 소금빵" },
  { categoryId: 3, name: "세계 챔피언 바리스타" },
  { categoryId: 4, name: "2026년도 신상 서울 카페" },
];

const STAR_COLORS: { value: StarColor; hex: string }[] = [
  { value: 'red', hex: '#E54B4B' },
  { value: 'pink', hex: '#FF8B8B' },
  { value: 'ivory', hex: '#F9F7E8' },
  { value: 'mint', hex: '#61BFAD' },
  { value: 'green', hex: '#167C80' },
  { value: 'sky', hex: '#B7E3E4' },
];

const mockFetchDetail = async (cafeid: string): Promise<CafeDetail> => {
  return new Promise((resolve) => {
    setTimeout(() => {
      resolve({
        id: cafeid,
        name: "아우어베이커리 역삼점",
        description: "더티초코, 빨미까레 등의 시그니처 메뉴와 특색 있는 경험을 파는 공간",
        rating: 3.8,
        reviewCount: 417,
        businessHours: "영업 중 12:00 ~ 24:00",
        address: "서울 마포구 포은로 63 형섭빌딩 2층",
        phone: "0503-7152-6912",
        imageUrls: [
          "/images/cafe/cafe1.png",
          "/images/cafe/cafe2.png",
          "/images/cafe/cafe1.png",
        ],
        menuList: [
          { name: "빨미까레", price: "5,500원", imageUrl: "/images/cafe/cafeMenu1.png" },
          { name: "더티초코", price: "5,800원", imageUrl: "/images/cafe/cafeMenu2.png" },
          { name: "빨미까레", price: "5,500원", imageUrl: "/images/cafe/cafeMenu1.png" },
        ]
      });
    }, 500);
  });
};

// ─────────────────────────────────────────────────────────
// 스크랩 생성 모달 (오버레이 안에서 띄움)
// ─────────────────────────────────────────────────────────
function CreateScrapModal({
  isOpen,
  onClose,
  onAdd,
}: {
  isOpen: boolean;
  onClose: () => void;
  onAdd: (name: string, color: StarColor) => void;
}) {
  const [name, setName] = useState("");
  const [selectedColor, setSelectedColor] = useState<StarColor>("red");
  const [error, setError] = useState("");

  const handleNameChange = (val: string) => {
    setName(val);
    if (val.length > 20) {
      setError("스크랩명은 20자 이내로 입력해주세요.");
    } else {
      setError("");
    }
  };

  const handleAdd = () => {
    if (!name.trim()) return;
    if (name.length > 20) return;
    onAdd(name.trim(), selectedColor);
    setName("");
    setSelectedColor("red");
    setError("");
    onClose();
  };

  const handleClose = () => {
    setName("");
    setSelectedColor("red");
    setError("");
    onClose();
  };

  return (
    <Modal isOpen={isOpen} onClose={handleClose} size="sm">
      <div className="flex flex-col gap-5">
        <h2 className="text-[16px] font-bold text-gray-900">스크랩명</h2>

        <Input
          placeholder="새로운 스크랩명을 입력하세요"
          value={name}
          onChange={(e) => handleNameChange((e.target as HTMLInputElement).value)}
          error={error}
        />

        {/* 컬러 선택 */}
        <div className="flex flex-col gap-2">
          <span className="text-[13px] font-medium text-gray-600">색상선택</span>
          <div className="flex gap-3">
            {STAR_COLORS.map((c) => (
              <button
                key={c.value}
                type="button"
                onClick={() => setSelectedColor(c.value)}
                className={`w-8 h-8 rounded-full flex items-center justify-center transition-all ${selectedColor === c.value
                  ? 'ring-2 ring-offset-2 ring-gray-400 scale-110'
                  : ''
                  }`}
                style={{ backgroundColor: c.hex }}
              >
                {selectedColor === c.value && (
                  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="white" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round">
                    <polyline points="20 6 9 17 4 12" />
                  </svg>
                )}
              </button>
            ))}
          </div>
        </div>

        {/* 하단 버튼 */}
        <div className="flex gap-3 mt-1">
          <Button
            variant="gray"
            size="full"
            onClick={handleClose}
            className="h-[48px] rounded-xl! text-gray-700!"
          >
            취소
          </Button>
          <Button
            variant="primary"
            size="full"
            onClick={handleAdd}
            className="h-[48px] rounded-xl! bg-[#ab353a]! text-white"
          >
            저장
          </Button>
        </div>
      </div>
    </Modal>
  );
}

// ─────────────────────────────────────────────────────────
// 저장 완료 토스트
// ─────────────────────────────────────────────────────────
function SavedToast({ isVisible, onClose }: { isVisible: boolean; onClose: () => void }) {
  if (!isVisible) return null;

  return (
    <div className="fixed top-6 left-1/2 -translate-x-1/2 z-[200] w-[340px] max-w-[90vw]">
      <div className="flex items-center gap-3 bg-white rounded-2xl shadow-[0_4px_20px_rgba(0,0,0,0.12)] border border-gray-100 px-5 py-4">
        <Info size={24} className="text-gray-600 shrink-0" />
        <span className="text-[15px] font-medium text-gray-800 flex-1">스크랩에 저장되었습니다.</span>
        <button
          type="button"
          onClick={onClose}
          className="shrink-0 p-0.5 text-gray-600 active:opacity-60"
        >
          <X size={22} strokeWidth={2} />
        </button>
      </div>
    </div>
  );
}

// ─────────────────────────────────────────────────────────
// 스크랩 카테고리 선택 오버레이
// ─────────────────────────────────────────────────────────
function ScrapCategoryOverlay({
  isOpen,
  onClose,
  categories,
  initialSelectedIds,
  onSave,
  onCreateCategory,
}: {
  isOpen: boolean;
  onClose: () => void;
  categories: ScrapCategoryOption[];
  initialSelectedIds: number[];
  onSave: (selectedIds: number[]) => void;
  onCreateCategory: (name: string, color: StarColor) => void;
}) {
  const [selectedIds, setSelectedIds] = useState<number[]>(initialSelectedIds);
  const [isCreateOpen, setIsCreateOpen] = useState(false);

  // 모달이 열릴 때마다 이전에 저장된 상태로 초기화 (저장 안 하고 닫았을 때 대비)
  useEffect(() => {
    if (isOpen) {
      setSelectedIds(initialSelectedIds);
    }
  }, [isOpen, initialSelectedIds]);

  const toggleCategory = (id: number) => {
    setSelectedIds((prev) =>
      prev.includes(id) ? prev.filter((v) => v !== id) : [...prev, id]
    );
  };

  const handleSave = () => {
    onSave(selectedIds);
    onClose();
  };

  if (!isOpen) return null;

  return (
    <>
      <div className="fixed inset-0 z-[100] flex flex-col">
        {/* 반투명 배경 */}
        <div className="absolute inset-0 bg-black/80" onClick={onClose} />

        {/* 콘텐츠 */}
        <div className="relative z-10 flex flex-col h-full max-w-[375px] mx-auto w-full">
          {/* X 닫기 버튼 - 우측 상단 더 위로 */}
          <div className="flex justify-end px-5 pt-8">
            <button
              type="button"
              onClick={onClose}
              className="p-1 text-white active:opacity-60 transition-opacity"
            >
              <X size={28} strokeWidth={2} />
            </button>
          </div>

          {/* SCRAP 타이틀 */}
          <div className="text-center mt-4 mb-10">
            <h2 className="text-[24px] font-bold text-white tracking-widest">SCRAP</h2>
          </div>

          {/* 카테고리 리스트 */}
          <div className="flex-1 overflow-y-auto px-6">
            <div className="flex flex-col">
              {categories.map((cat) => {
                const isSelected = selectedIds.includes(cat.categoryId);
                return (
                  <button
                    key={cat.categoryId}
                    type="button"
                    onClick={() => toggleCategory(cat.categoryId)}
                    className="flex items-center justify-center py-4 border-t border-white/30 active:bg-white/5 transition-colors relative"
                  >
                    <span className="text-[16px] font-medium text-white">{cat.name}</span>
                    {isSelected && (
                      <Check size={22} strokeWidth={2.5} className="text-white absolute right-2" />
                    )}
                  </button>
                );
              })}
              <div className="border-t border-white/30" />
            </div>
          </div>

          {/* 하단 버튼 영역 - 흰색 배경 */}
          <div className="px-8 py-6 pb-24 flex gap-3">
            <button
              type="button"
              onClick={() => setIsCreateOpen(true)}
              className="flex-1 h-[48px] rounded-full bg-white text-gray-700 text-[15px] font-medium active:bg-gray-100 transition-colors shadow-[0_2px_12px_rgba(0,0,0,0.12)]"
            >
              생성
            </button>
            <button
              type="button"
              onClick={handleSave}
              className="flex-1 h-[48px] rounded-full bg-white border border-[#C3304F] text-[#C3304F] text-[15px] font-bold active:bg-red-50 transition-colors shadow-[0_2px_12px_rgba(0,0,0,0.12)]"
            >
              저장
            </button>
          </div>
        </div>
      </div>

      {/* 새 카테고리 생성 모달 */}
      <CreateScrapModal
        isOpen={isCreateOpen}
        onClose={() => setIsCreateOpen(false)}
        onAdd={(name, color) => {
          onCreateCategory(name, color);
        }}
      />
    </>
  );
}

export default function CafeDetailPage({ params }: { params: Promise<{ cafeid: string }> | { cafeid: string } }) {
  const router = useRouter();
  const [cafe, setCafe] = useState<CafeDetail | null>(null);
  const [isScrapOpen, setIsScrapOpen] = useState(false);
  const [isScrapped, setIsScrapped] = useState(false);
  const [savedCategoryIds, setSavedCategoryIds] = useState<number[]>([]);
  const [showSavedToast, setShowSavedToast] = useState(false);
  const [scrapCategories, setScrapCategories] = useState<ScrapCategoryOption[]>(MOCK_SCRAP_CATEGORIES);

  // Slider State
  const [currentIndex, setCurrentIndex] = useState(0);
  const [direction, setDirection] = useState(0);

  const resolvedParams = params instanceof Promise ? use(params) : params;
  const cafeid = resolvedParams.cafeid;

  useEffect(() => {
    if (cafeid) {
      mockFetchDetail(cafeid).then(setCafe);
    }
  }, [cafeid]);

  const handleScrapSave = (selectedIds: number[]) => {
    setSavedCategoryIds(selectedIds);
    if (selectedIds.length > 0) {
      setIsScrapped(true);
      setShowSavedToast(true);
      setTimeout(() => setShowSavedToast(false), 3000);
    } else {
      setIsScrapped(false);
    }
    console.log('Saved to categories:', selectedIds);
  };

  const handleCreateCategory = (name: string, color: StarColor) => {
    const newCat: ScrapCategoryOption = {
      categoryId: Date.now(),
      name,
    };
    setScrapCategories((prev) => [...prev, newCat]);
    // Optionally automatically select the newly created category if needed later
  };

  if (!cafe) {
    return (
      <div className="w-full h-[100dvh] flex items-center justify-center bg-bg_white text-gray-500 font-pretendard">
        로딩 중...
      </div>
    );
  }

  return (
    <motion.div
      initial={{ y: 20, opacity: 0 }}
      animate={{ y: 0, opacity: 1 }}
      transition={{ duration: 0.4, ease: "easeOut" }}
      className="w-full min-h-full bg-white font-pretendard flex flex-col pt-safe-top pb-8"
    >
      {/* 상단 비주얼 영역 (슬라이더) */}
      <div className="relative w-full h-[360px] shrink-0 overflow-hidden touch-pan-y bg-gray-100">
        <AnimatePresence initial={false} custom={direction}>
          <motion.div
            key={currentIndex}
            custom={direction}
            variants={{
              enter: (dir: number) => ({
                x: dir > 0 ? 100 : -100,
                opacity: 0,
                zIndex: 1,
              }),
              center: {
                zIndex: 1,
                x: 0,
                opacity: 1,
              },
              exit: (dir: number) => ({
                zIndex: 0,
                x: dir > 0 ? -50 : 50,
                opacity: 0,
              }),
            }}
            initial="enter"
            animate="center"
            exit="exit"
            transition={{
              x: { type: "spring", stiffness: 300, damping: 30 },
              opacity: { duration: 0.3 },
            }}
            className="absolute inset-0 w-full h-full cursor-grab active:cursor-grabbing"
            drag="x"
            dragConstraints={{ left: 0, right: 0 }}
            dragElastic={0.2}
            onDragEnd={(e, { offset, velocity }) => {
              const swipe = offset.x;
              if (swipe < -50 || velocity.x < -500) {
                setDirection(1);
                setCurrentIndex((prev) => (prev + 1) % cafe.imageUrls.length);
              } else if (swipe > 50 || velocity.x > 500) {
                setDirection(-1);
                setCurrentIndex((prev) => (prev - 1 + cafe.imageUrls.length) % cafe.imageUrls.length);
              }
            }}
          >
            <Image
              src={cafe.imageUrls[currentIndex]}
              alt={`${cafe.name} 이미지 ${currentIndex + 1}`}
              fill
              className="object-cover pointer-events-none"
              draggable={false}
              priority={currentIndex === 0}
            />
          </motion.div>
        </AnimatePresence>

        {/* 뒤로가기 버튼 */}
        <button
          onClick={() => router.back()}
          className="absolute top-4 left-4 z-20 w-10 h-10 flex items-center justify-center cursor-pointer hover:opacity-80 transition-opacity pointer-events-auto"
        >
          <Image src="/images/map/backIcon.png" alt="뒤로가기" width={40} height={40} className="w-10 h-10 object-contain drop-shadow-md pointer-events-none" draggable={false} />
        </button>

        {/* 스크랩(별) 버튼 - 저장 여부에 따라 아이콘 변경 */}
        <button
          onClick={() => setIsScrapOpen(true)}
          className="absolute top-4 right-4 z-20 w-10 h-10 flex items-center justify-center cursor-pointer hover:opacity-80 transition-opacity pointer-events-auto"
        >
          <Image
            src={isScrapped ? "/images/map/scrappedIcon.png" : "/images/map/unscrappedIcon.png"}
            alt="스크랩"
            width={40}
            height={40}
            className="w-10 h-10 object-contain drop-shadow-md pointer-events-none"
            draggable={false}
          />
        </button>

        {/* 하단 그라데이션 및 정보 오버레이 */}
        <div className="absolute inset-x-0 bottom-0 h-48 bg-gradient-to-t from-black/80 to-transparent flex flex-col justify-end px-5 pb-8 text-white z-10 pointer-events-none">
          <h1 className="text-[24px] font-semibold mb-2">{cafe.name}</h1>
          <p className="text-[14px] text-gray-200 leading-snug w-[90%]">{cafe.description}</p>
        </div>

        {/* 인디케이터 */}
        <div className="absolute bottom-4 inset-x-0 flex justify-center items-center gap-1.5 z-20 pointer-events-none">
          {cafe.imageUrls.map((_, idx) => (
            <div
              key={idx}
              className={`h-1.5 rounded-full shadow-sm transition-all duration-300 ${idx === currentIndex ? 'w-4 bg-white' : 'w-1.5 bg-white/50'
                }`}
            />
          ))}
        </div>
      </div>

      {/* 바디 컨텐츠 */}
      <div className="flex-1">
        {/* 리뷰 평점 */}
        <div className="px-5 py-5 flex items-center justify-between border-b border-gray-100">
          <div className="flex items-center gap-1.5">
            <Image src="/images/map/reviewStarIcon.png" alt="평점" width={20} height={20} className="w-5 h-5 object-contain" />
            <span className="text-[17px] font-medium text-gray-900">{cafe.rating}</span>
          </div>
          <button
            onClick={() => router.push(`/cafes/${cafeid}/reviews`)}
            className="flex items-center text-gray-900 text-[15px] font-medium hover:text-gray-600 transition-colors"
          >
            Review {cafe.reviewCount} <span className="ml-1.5 text-gray-400 font-light">&gt;</span>
          </button>
        </div>

        {/* 기본 정보 */}
        <div className="px-5 py-6 border-b border-gray-100 border-b-[8px]">
          <h2 className="text-[16px] font-bold text-gray-900 mb-4">기본 정보</h2>
          <div className="space-y-3.5">
            <div className="flex items-center gap-2.5">
              <Image src="/images/map/clockIcon.png" alt="영업시간" width={20} height={20} className="w-5 h-5 object-contain" />
              <span className="text-gray-900 text-[14px] font-medium">{cafe.businessHours}</span>
            </div>
            <div className="flex items-center gap-2.5">
              <Image src="/images/map/locationIcon.png" alt="주소" width={20} height={20} className="w-5 h-5 object-contain" />
              <span className="text-gray-900 text-[14px] font-medium">{cafe.address}</span>
            </div>
            <div className="flex items-center gap-2.5">
              <Image src="/images/map/phoneIcon.png" alt="전화번호" width={20} height={20} className="w-5 h-5 object-contain" />
              <span className="text-gray-900 text-[14px] font-medium">{cafe.phone}</span>
            </div>
          </div>
        </div>

        {/* 메뉴 */}
        <div className="px-5 py-6">
          <h2 className="text-[16px] font-bold text-gray-900 mb-5">메뉴</h2>
          <div className="space-y-5">
            {cafe.menuList && cafe.menuList.length > 0 ? (
              cafe.menuList.map((menu, idx) => (
                <div key={idx} className="flex gap-4 cursor-pointer hover:bg-gray-50/50 p-1 -m-1 rounded-xl transition-colors">
                  <div className="w-24 h-24 relative shrink-0">
                    <Image src={menu.imageUrl} alt={menu.name} fill className="object-cover rounded-xl" />
                  </div>
                  <div className="flex flex-col justify-center">
                    <h3 className="text-[16px] font-bold text-gray-900 mb-1.5">{menu.name}</h3>
                    <p className="text-[15px] font-medium text-gray-900">{menu.price}</p>
                  </div>
                </div>
              ))
            ) : (
              <div className="py-12 flex flex-col items-center justify-center bg-gray-50 rounded-2xl border border-dashed border-gray-200">
                <p className="text-[14px] text-gray-500 font-medium">현재 메뉴 정보 수집 중입니다.</p>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* 스크랩 카테고리 선택 오버레이 */}
      <ScrapCategoryOverlay
        isOpen={isScrapOpen}
        onClose={() => setIsScrapOpen(false)}
        categories={scrapCategories}
        initialSelectedIds={savedCategoryIds}
        onSave={handleScrapSave}
        onCreateCategory={handleCreateCategory}
      />

      {/* 저장 완료 토스트 */}
      <SavedToast
        isVisible={showSavedToast}
        onClose={() => setShowSavedToast(false)}
      />
    </motion.div>
  );
}
