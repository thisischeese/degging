'use client';

import { useState } from "react";
import Image from "next/image";
import { useRouter } from "next/navigation";
import { MapPin, MoreVertical, X } from "lucide-react";
import Header from "@/common/components/Header";
import Modal from "@/common/components/Modal";
import Button from "@/common/components/Button";
import { ScrapCafeItem } from "@/features/scraps/types";

// ─────────────────────────────────────────────────────────
// Mock 데이터 (API 연동 전 임시)
// ─────────────────────────────────────────────────────────
const MOCK_CAFES: ScrapCafeItem[] = [
    {
        cafeId: 1,
        name: "아우어베이커리 역삼점",
        description: "조용하고 넓은 공간에서 즐기는 시그니처 빵",
        address: "서울 강남구 언주로85길 29 1층",
        imageUrl: "/images/curation/mangoBingsu.png",
    },
    {
        cafeId: 2,
        name: "리파인 망원 (REFINE)",
        description: "망리단길에 위치한 캐주얼 다이닝",
        address: "서울특별시 마포구 망원동",
        imageUrl: "/images/curation/mangoBingsu.png",
    },
    {
        cafeId: 3,
        name: "아우어베이커리 역삼점",
        description: "조용하고 넓은 공간에서 즐기는 시그니처 빵",
        address: "서울 강남구 언주로85길 29 1층",
        imageUrl: "/images/curation/mangoBingsu.png",
    },
    {
        cafeId: 4,
        name: "아우어베이커리 역삼점",
        description: "조용하고 넓은 공간에서 즐기는 시그니처 빵",
        address: "서울 강남구 언주로85길 29 1층",
        imageUrl: "/images/curation/mangoBingsu.png",
    },
    {
        cafeId: 5,
        name: "서울 신라 호텔",
        description: "호텔에 걸맞는 망고 빙수의 정수",
        address: "서울 중구 동호로 249",
        imageUrl: "/images/curation/mangoBingsu.png",
    },
];

// ─────────────────────────────────────────────────────────
// 카페 삭제 확인 모달
// ─────────────────────────────────────────────────────────
function DeleteCafeConfirmModal({
    isOpen,
    onClose,
    onDelete,
}: {
    isOpen: boolean;
    onClose: () => void;
    onDelete: () => void;
}) {
    return (
        <Modal isOpen={isOpen} onClose={onClose} size="sm">
            <div className="flex flex-col items-center gap-6 py-4">
                <p className="text-[15px] font-medium text-gray-800 text-center">
                    해당 카페를 삭제하시겠습니까?
                </p>
                <div className="flex gap-3 w-full">
                    <Button
                        variant="gray"
                        size="full"
                        onClick={onClose}
                        className="h-[48px] rounded-xl! text-gray-700!"
                    >
                        취소
                    </Button>
                    <Button
                        variant="primary"
                        size="full"
                        onClick={onDelete}
                        className="h-[48px] rounded-xl! bg-[#ab353a]! text-white"
                    >
                        삭제
                    </Button>
                </div>
            </div>
        </Modal>
    );
}

// ─────────────────────────────────────────────────────────
// 카페 아이템 카드
// ─────────────────────────────────────────────────────────
function ScrapCafeCard({
    cafe,
    isDeleteMode,
    onDeleteClick,
    onClick,
}: {
    cafe: ScrapCafeItem;
    isDeleteMode: boolean;
    onDeleteClick: () => void;
    onClick: () => void;
}) {
    return (
        <div
            onClick={isDeleteMode ? undefined : onClick}
            className="flex items-center gap-4 bg-white rounded-2xl p-4 border border-gray-100 shadow-sm active:bg-gray-50 transition-colors cursor-pointer"
        >
            {/* 썸네일 */}
            <div className="relative w-[76px] h-[76px] shrink-0 rounded-xl overflow-hidden bg-gray-100">
                <Image
                    src={cafe.imageUrl}
                    alt={cafe.name}
                    fill
                    className="object-cover"
                    unoptimized
                />
            </div>

            {/* 텍스트 영역 */}
            <div className="flex flex-col flex-1 min-w-0 justify-center gap-1">
                <h3 className="font-bold text-[14px] text-gray-900 truncate">{cafe.name}</h3>
                <p className="text-[12px] text-gray-500 truncate">{cafe.description}</p>
                <div className="flex items-center gap-1 text-gray-400 mt-0.5">
                    <MapPin size={12} className="shrink-0" />
                    <span className="text-[12px] truncate">{cafe.address}</span>
                </div>
            </div>

            {/* 삭제 모드 X 버튼 */}
            {isDeleteMode && (
                <button
                    type="button"
                    onClick={(e) => {
                        e.stopPropagation();
                        onDeleteClick();
                    }}
                    className="shrink-0 p-1 text-[#ab353a] active:opacity-60 transition-opacity"
                    aria-label="삭제"
                >
                    <X size={20} strokeWidth={2} />
                </button>
            )}
        </div>
    );
}

// ─────────────────────────────────────────────────────────
// 메인 스크랩 상세 페이지
// ─────────────────────────────────────────────────────────
export default function ScrapDetailPage({
    params,
}: {
    params: { categoryId: string };
}) {
    const router = useRouter();
    const categoryName = "역삼역 근처"; // TODO: params.categoryId로 API 조회

    const [cafes, setCafes] = useState<ScrapCafeItem[]>(MOCK_CAFES);
    const [isMenuOpen, setIsMenuOpen] = useState(false);
    const [isDeleteMode, setIsDeleteMode] = useState(false);
    const [deletingCafeId, setDeletingCafeId] = useState<number | null>(null);

    const handleDeleteCafe = () => {
        if (deletingCafeId === null) return;
        setCafes((prev) => prev.filter((c) => c.cafeId !== deletingCafeId));
        setDeletingCafeId(null);
    };

    return (
        <div className="flex flex-col min-h-full bg-bg_white font-pretendard overflow-x-hidden">

            {/* ── 헤더 ── */}
            <div className="relative">
                <Header
                    leftContent="back"
                    centerContent={categoryName}
                    rightContent={
                        isDeleteMode ? (
                            <button
                                type="button"
                                onClick={() => setIsDeleteMode(false)}
                                className="text-[15px] font-medium text-gray-800 p-1 active:opacity-50 transition-opacity"
                            >
                                완료
                            </button>
                        ) : (
                            <button
                                type="button"
                                onClick={() => setIsMenuOpen((prev) => !prev)}
                                className="p-1 active:opacity-50 transition-opacity"
                            >
                                <MoreVertical size={22} className="text-gray-700" />
                            </button>
                        )
                    }
                />

                {/* 케밥 드롭다운 */}
                {isMenuOpen && !isDeleteMode && (
                    <>
                        <div
                            className="fixed inset-0 z-40"
                            onClick={() => setIsMenuOpen(false)}
                        />
                        <div className="absolute right-4 top-14 z-50">
                            <div className="w-[140px] bg-white border border-gray-200 rounded-[12px] shadow-[0_4px_16px_rgba(0,0,0,0.10)] overflow-hidden flex flex-col">
                                <button
                                    type="button"
                                    onClick={() => {
                                        // TODO: 추천(링크 공유) 기능 연동
                                        setIsMenuOpen(false);
                                    }}
                                    className="w-full text-center px-4 py-3 text-[14px] font-medium text-gray-800 transition-colors active:bg-gray-50 border-b border-gray-100"
                                >
                                    추천
                                </button>
                                <button
                                    type="button"
                                    onClick={() => {
                                        setIsDeleteMode(true);
                                        setIsMenuOpen(false);
                                    }}
                                    className="w-full text-center px-4 py-3 text-[14px] font-medium text-[#ab353a] transition-colors active:bg-red-50"
                                >
                                    삭제
                                </button>
                            </div>
                        </div>
                    </>
                )}
            </div>

            {/* ── 카페 리스트 ── */}
            <div className="flex flex-col gap-3 px-5 pt-4 pb-24">
                {cafes.length > 0 ? (
                    cafes.map((cafe) => (
                        <ScrapCafeCard
                            key={cafe.cafeId}
                            cafe={cafe}
                            isDeleteMode={isDeleteMode}
                            onDeleteClick={() => setDeletingCafeId(cafe.cafeId)}
                            onClick={() => router.push(`/cafes/${cafe.cafeId}`)}
                        />
                    ))
                ) : (
                    <div className="flex flex-col items-center justify-center py-20 text-gray-400">
                        <p className="text-[14px]">스크랩된 카페가 없습니다.</p>
                    </div>
                )}
            </div>

            {/* ── 삭제 확인 모달 ── */}
            <DeleteCafeConfirmModal
                isOpen={deletingCafeId !== null}
                onClose={() => setDeletingCafeId(null)}
                onDelete={handleDeleteCafe}
            />
        </div>
    );
}
