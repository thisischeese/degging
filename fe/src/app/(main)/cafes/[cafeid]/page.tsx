'use client';

import React, { useEffect, useState, use } from 'react';
import { useRouter } from 'next/navigation';
import Image from 'next/image';
import { motion, AnimatePresence } from 'framer-motion';
import { X, Check, Info } from 'lucide-react';
import Modal from '@/common/components/Modal';
import Button from '@/common/components/Button';
import { Input } from '@/common/components/Input';
import { StarColor, ScrapList } from '@/features/scraps/types';
import { useSuspenseQuery } from '@tanstack/react-query';
import { getCafeDetail } from '@/features/cafes/api/cafeApi';
import { getScraps, postCreateScrap, postScrapCafe, postScrapCafeToAll, deleteScrapCafe, getScrapDetail } from '@/features/scraps/api/scrapApi';
import { Chip } from '@/common/components/Chip';




const STAR_COLORS: { value: StarColor; hex: string }[] = [
  { value: 'RED', hex: '#E54B4B' },
  { value: 'PINK', hex: '#FF8B8B' },
  { value: 'IVORY', hex: '#F9F7E8' },
  { value: 'MINT', hex: '#61BFAD' },
  { value: 'GREEN', hex: '#167C80' },
  { value: 'SKY', hex: '#B7E3E4' },
];


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
  const [selectedColor, setSelectedColor] = useState<StarColor>("RED");
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
    setSelectedColor("RED");
    setError("");
    onClose();
  };

  const handleClose = () => {
    setName("");
    setSelectedColor("RED");
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
  categories: ScrapList[];
  initialSelectedIds: string[];
  onSave: (selectedIds: string[]) => void;
  onCreateCategory: (name: string, color: StarColor) => void;
}) {
  // key={`${isScrapOpen}-${savedCategoryIds.join(',')}`} prop이 변경될 때마다 컴포넌트가 리마운트되므로
  // initialSelectedIds를 그대로 초기값으로 사용 (useEffect 내 setState 불필요 → lint 수정)
  const [selectedIds, setSelectedIds] = useState<string[]>(initialSelectedIds);
  const [isCreateOpen, setIsCreateOpen] = useState(false);

  const toggleCategory = (id: string) => {
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
                const isDefault = cat.scrapId === null;
                const isSelected = isDefault || selectedIds.includes(cat.scrapId as string);

                return (
                  <button
                    key={cat.scrapId ?? 'default'}
                    type="button"
                    onClick={() => {
                      if (!isDefault) toggleCategory(cat.scrapId as string);
                    }}
                    className={`flex items-center justify-center py-4 border-t border-white/30 transition-colors relative ${!isDefault ? 'active:bg-white/5' : 'cursor-default'}`}
                  >
                    <span className={`text-[16px] text-white ${isDefault ? 'font-bold' : 'font-medium'}`}>
                      {isDefault ? '기본 스크랩' : cat.name}
                    </span>
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
  const resolvedParams = params instanceof Promise ? use(params) : params;
  const cafeid = resolvedParams.cafeid;

  // [수정] 실제 API 연동 쿼리
  const { data: cafe } = useSuspenseQuery({
    queryKey: ['cafeDetail', cafeid],
    queryFn: () => getCafeDetail(cafeid),
  });

  const [isScrapOpen, setIsScrapOpen] = useState(false);
  const [isScrapped, setIsScrapped] = useState(cafe.scrapped ?? cafe.isScrapped ?? false);
  const [savedCategoryIds, setSavedCategoryIds] = useState<string[]>([]);
  const [showSavedToast, setShowSavedToast] = useState(false);
  const [scrapCategories, setScrapCategories] = useState<ScrapList[]>([]);

  // Slider State
  const [currentIndex, setCurrentIndex] = useState(0);
  const [direction, setDirection] = useState(0);

  // 카페 상세 진입 시 또는 모달 열 시 카테고리 로딩 및 해당하는지 검사
  useEffect(() => {
    if (isScrapOpen && scrapCategories.length === 0) {
      getScraps().then(async data => {
        // null을 갖는 기본 스크랩을 포함하여 가져오고 맨 앞으로 정렬
        const sorted = [...data].sort((a, b) => {
          if (a.scrapId === null) return -1;
          if (b.scrapId === null) return 1;
          return 0;
        });
        setScrapCategories(sorted);

        // 해당 카페가 이미 저장된 스크랩 카테고리 ID들을 찾기 위해 각 카테고리 상세 조회
        const activeIds: string[] = [];
        await Promise.all(
          data.filter(c => c.scrapId !== null).map(async (cat) => {
            try {
              const detail = await getScrapDetail(cat.scrapId as string);
              if (detail.cafes.some(c => String(c.cafeId) === String(cafeid))) {
                activeIds.push(cat.scrapId as string);
              }
            } catch (err) {
              console.error(`스크랩 상세 로드 실패 (ID: ${cat.scrapId})`, err);
            }
          })
        );
        setSavedCategoryIds(activeIds);

      }).catch(err => console.error('스크랩 카테고리 로드 실패', err));
    }
  }, [isScrapOpen, scrapCategories.length, cafeid]);

  const handleScrapSave = async (selectedIds: string[]) => {
    try {
      // 1. 처음 스크랩하는 경우에만 기본 스크랩 API 전송 (중복 전송 방지)
      if (!isScrapped) {
        try {
          await postScrapCafeToAll(cafeid);
        } catch (e) {
          console.warn('기본 스크랩 담기 건너뜀 (API 미구현 혹은 에러):', e);
        }
        setIsScrapped(true); // 에러가 나더라도 UI상 스크랩 된 것으로 처리하고 아래 폴더 작업 진행
      }

      // 2. 새로 추가된 폴더 찾기 (selectedIds에는 있는데 기존 savedCategoryIds에는 없는 것)
      const addedIds = selectedIds.filter(id => !savedCategoryIds.includes(id));
      
      // 3. 체크 해제된 폴더 찾기 (기존 savedCategoryIds에는 있는데 selectedIds에는 없는 것)
      const removedIds = savedCategoryIds.filter(id => !selectedIds.includes(id));

      // 추가와 삭제를 동시에 병렬로 백엔드 전송
      await Promise.all([
        ...addedIds.map(id => postScrapCafe(id, cafeid)),
        ...removedIds.map(id => deleteScrapCafe(id, cafeid))
      ]);

      // 프론트엔드 상태 동기화
      setSavedCategoryIds(selectedIds);

      setShowSavedToast(true);
      setTimeout(() => setShowSavedToast(false), 3000);
    } catch (err) {
      console.error('스크랩 저장 실패', err);
    }
  };

  const handleCreateCategory = async (name: string, color: StarColor) => {
    try {
      await postCreateScrap({ name, color });
      const updated = await getScraps();
      // null을 갖는 기본 스크랩을 맨 앞으로 정렬 후 저장
      const sorted = [...updated].sort((a, b) => {
        if (a.scrapId === null) return -1;
        if (b.scrapId === null) return 1;
        return 0;
      });
      setScrapCategories(sorted);
    } catch (err) {
      console.error('카테고리 생성 실패', err);
    }
  };


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
                setCurrentIndex((prev) => (prev + 1) % (cafe.images?.length || 1));
              } else if (swipe > 50 || velocity.x > 500) {
                setDirection(-1);
                setCurrentIndex((prev) => (prev - 1 + (cafe.images?.length || 1)) % (cafe.images?.length || 1));
              }
            }}
          >
            {/* 
            <Image
              src={cafe.images?.[currentIndex] || "/images/cafe/cafe1.png"}
              alt={`${cafe.name} 이미지 ${currentIndex + 1}`}
              fill
              className="object-cover pointer-events-none"
              draggable={false}
              priority={currentIndex === 0}
            />
            */}
            <Image
              src={
                cafe.images && cafe.images.length > 0
                  ? cafe.images[currentIndex]
                  : "/images/cafe/cafe1.png"
              }
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

        {/* 스크랩(별) 버튼 - 저장 여부 및 색상에 따라 아이콘 변경 가능, 기본 스크랩 이미지를 쓰다가 추후 색상 반영 가능 */}
        <button
          onClick={() => setIsScrapOpen(true)}
          className="absolute top-4 right-4 z-20 w-10 h-10 flex items-center justify-center cursor-pointer hover:opacity-80 transition-opacity pointer-events-auto"
        >
          {isScrapped ? (
            // 스크랩 시 항상 RED(#E54B4B) 고정 - 여러 폴더에 담아도 통일감 있게 표시
            <div className="w-10 h-10 flex items-center justify-center rounded-full bg-white/20 backdrop-blur-md">
              <svg width="24" height="24" viewBox="0 0 24 24" fill="#E54B4B" stroke="none" className="drop-shadow-md">
                <path d="M12 2L15.09 8.26L22 9.27L17 14.14L18.18 21.02L12 17.77L5.82 21.02L7 14.14L2 9.27L8.91 8.26L12 2Z" />
              </svg>
            </div>
          ) : (
            <Image
              src={"/images/map/unscrappedIcon.png"}
              alt="스크랩 전"
              width={40}
              height={40}
              className="w-10 h-10 object-contain drop-shadow-md pointer-events-none"
              draggable={false}
            />
          )}
        </button>

        {/* 하단 그라데이션 및 정보 오버레이 */}
        <div className="absolute inset-x-0 bottom-0 h-48 bg-gradient-to-t from-black/80 to-transparent flex flex-col justify-end px-5 pb-8 text-white z-10 pointer-events-none">
          <h1 className="text-[24px] font-semibold mb-2">{cafe.name}</h1>
          {/* <p className="text-[14px] text-gray-200 leading-snug w-[90%] mb-2 opacity-80">{cafe.description || "등록된 카페 소개가 없습니다."}</p> */}
          <p className="text-[14px] text-gray-200 leading-snug w-[90%] mb-2 opacity-80">{cafe.cafeIntro || "등록된 카페 소개가 없습니다."}</p>
          {/* 바이브 태그 렌더링 */}
          <div className="flex gap-2 flex-wrap">
            {cafe.vibeTags?.map((tag, i) => (
              <Chip key={i} label={`# ${tag}`} variant="map" isActive={true} />
            ))}
          </div>
        </div>

        {/* 인디케이터 */}
        <div className="absolute bottom-4 inset-x-0 flex justify-center items-center gap-1.5 z-20 pointer-events-none">
          {cafe.images?.map((_, idx) => (
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
        <div className="px-5 py-6 border-b-8 border-gray-100">
          <h2 className="text-[16px] font-bold text-gray-900 mb-4">기본 정보</h2>
          <div className="space-y-3.5">
            <div className="flex items-center gap-2.5">
              <Image src="/images/map/clockIcon.png" alt="영업시간" width={20} height={20} className="w-5 h-5 object-contain" />
              <span className="text-gray-900 text-[14px] font-medium">{cafe.businessHours || "연중무휴"}</span>
            </div>
            <div className="flex items-center gap-2.5">
              <Image src="/images/map/locationIcon.png" alt="주소" width={20} height={20} className="w-5 h-5 object-contain" />
              <span className="text-gray-900 text-[14px] font-medium">{cafe.roadAddress || cafe.address || "주소 미등록"}</span>
            </div>
            <div className="flex items-center gap-2.5">
              <Image src="/images/map/phoneIcon.png" alt="전화번호" width={20} height={20} className="w-5 h-5 object-contain" />
              <span className="text-gray-900 text-[14px] font-medium">{cafe.phone || "전화번호 미등록"}</span>
            </div>
          </div>
        </div>

        {/* 메뉴 */}
        <div className="px-5 py-6">
          <h2 className="text-[16px] font-bold text-gray-900 mb-5">메뉴</h2>
          <div className="space-y-5">
            {cafe.menus && cafe.menus.length > 0 ? (
              cafe.menus.map((menu, idx) => (
                <div key={idx} className="flex gap-4 p-1 -m-1 rounded-xl">
                  {/* API에 메뉴 이미지가 없으므로 이미지 렌더링 부분 생략 혹은 플레이스홀더 */}
                  {/* 
                  <div className="w-24 h-24 relative shrink-0 bg-gray-100 rounded-xl flex items-center justify-center">
                    <span className="text-xs text-gray-400">No Image</span>
                  </div>
                  */}
                  <div className="w-24 h-24 relative shrink-0 bg-gray-100 rounded-xl flex items-center justify-center overflow-hidden">
                    <Image
                      src={menu.image || '/images/common/logo.png'}
                      alt={menu.menuName || menu.name || '메뉴 이미지'}
                      fill
                      className={`${menu.image ? 'object-cover' : 'object-contain p-4'}`}
                      unoptimized
                    />
                  </div>
                  <div className="flex flex-col justify-center">
                    {/* <h3 className="text-[16px] font-bold text-gray-900 mb-1.5">{menu.name}</h3> */}
                    <h3 className="text-[16px] font-bold text-gray-900 mb-1.5">{menu.menuName || menu.name}</h3>
                    {/* <p className="text-[15px] font-medium text-gray-900">{typeof menu.price === 'number' ? \`\${menu.price.toLocaleString()}원\` : menu.price}</p> */}
                    <p className="text-[15px] font-medium text-gray-900">
                      {typeof menu.price === 'number' 
                        ? `${menu.price.toLocaleString()}원` 
                        : (menu.price || '가격 변동')}
                    </p>
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
        key={`${isScrapOpen}-${savedCategoryIds.join(',')}`}
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
