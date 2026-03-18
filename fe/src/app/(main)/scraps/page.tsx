'use client';

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import Image from "next/image";
import Header from "@/common/components/Header";
import Modal from "@/common/components/Modal";
import Button from "@/common/components/Button";
import { Input } from "@/common/components/Input";
import { ScrapCategory, StarColor } from "@/features/scraps/types";
import { Plus, MoreVertical, Star, Pencil, Trash2 } from "lucide-react";

// ─────────────────────────────────────────────────────────
// 별 색상 매핑
// ─────────────────────────────────────────────────────────
const STAR_COLOR_MAP: Record<StarColor, string> = {
    red: '#E54B4B',
    pink: '#FF8B8B',
    ivory: '#F9F7E8',
    mint: '#61BFAD',
    green: '#167C80',
    sky: '#B7E3E4',
};

const STAR_COLORS: { value: StarColor; hex: string }[] = [
    { value: 'red', hex: '#E54B4B' },
    { value: 'pink', hex: '#FF8B8B' },
    { value: 'ivory', hex: '#F9F7E8' },
    { value: 'mint', hex: '#61BFAD' },
    { value: 'green', hex: '#167C80' },
    { value: 'sky', hex: '#B7E3E4' },
];

// ─────────────────────────────────────────────────────────
// Mock 데이터 (API 연동 전 임시)
// ─────────────────────────────────────────────────────────
const MOCK_CATEGORIES: ScrapCategory[] = [
    {
        categoryId: 1,
        name: "역삼역 근처",
        starColor: "red",
        thumbnails: [
            { cafeId: 1, imageUrl: "/images/curation/mangoBingsu.png" },
            { cafeId: 2, imageUrl: "/images/curation/mangoBingsu.png" },
            { cafeId: 3, imageUrl: "/images/curation/mangoBingsu.png" },
        ],
    },
    {
        categoryId: 2,
        name: "연남 분좋카 투어",
        starColor: "pink",
        thumbnails: [],
    },
    {
        categoryId: 3,
        name: "소금빵 맛집",
        starColor: "ivory",
        thumbnails: [],
    },
    {
        categoryId: 4,
        name: "대전 빵지순례",
        starColor: "green",
        thumbnails: [],
    },
];

// ─────────────────────────────────────────────────────────
// 썸네일 그리드 컴포넌트 (카테고리 카드 내부)
// ─────────────────────────────────────────────────────────
function ThumbnailGrid({ thumbnails }: { thumbnails: { cafeId: number; imageUrl: string }[] }) {
    const slots = thumbnails.slice(0, 4);

    return (
        <div className="w-full aspect-square rounded-[20px] bg-white shadow-[0_2px_8px_rgba(0,0,0,0.08)] p-[5px]">
            <div className="w-full h-full grid grid-cols-2 grid-rows-2 gap-[4px]">
                <div className="relative overflow-hidden rounded-[12px] bg-white">
                    {slots[0] && <Image src={slots[0].imageUrl} alt="스크랩 1" fill className="object-cover" />}
                </div>
                <div className="relative overflow-hidden rounded-[12px] bg-white">
                    {slots[1] && <Image src={slots[1].imageUrl} alt="스크랩 2" fill className="object-cover" />}
                </div>
                <div className="relative overflow-hidden rounded-[12px] bg-white">
                    {slots[2] && <Image src={slots[2].imageUrl} alt="스크랩 3" fill className="object-cover" />}
                </div>
                <div className="relative overflow-hidden rounded-[12px] bg-white">
                    {slots[3] && <Image src={slots[3].imageUrl} alt="스크랩 4" fill className="object-cover" />}
                </div>
            </div>
        </div>
    );
}

// ─────────────────────────────────────────────────────────
// 새 카테고리 추가 모달
// ─────────────────────────────────────────────────────────
function NewCategoryModal({
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

    const handleAdd = () => {
        if (!name.trim()) return;
        onAdd(name.trim(), selectedColor);
        setName("");
        setSelectedColor("red");
        onClose();
    };

    return (
        <Modal isOpen={isOpen} onClose={onClose} size="sm">
            <div className="flex flex-col gap-5">
                <h2 className="text-[16px] font-bold text-gray-900">새로운 카테고리</h2>

                <Input
                    placeholder="카테고리 이름을 입력하세요"
                    value={name}
                    onChange={(e) => setName((e.target as HTMLInputElement).value)}
                />

                {/* 컬러 선택 */}
                <div className="flex flex-col gap-2">
                    <span className="text-[13px] font-medium text-gray-600">아이콘 색상</span>
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
                        onClick={onClose}
                        className="h-[48px] rounded-xl! text-gray-700!"
                    >
                        취소
                    </Button>
                    <Button
                        variant="primary"
                        size="full"
                        onClick={handleAdd}
                        className="h-[48px] rounded-xl!"
                    >
                        추가
                    </Button>
                </div>
            </div>
        </Modal>
    );
}

// ─────────────────────────────────────────────────────────
// 카테고리 수정 모달
// ─────────────────────────────────────────────────────────
function EditCategoryModal({
    isOpen,
    onClose,
    onEdit,
    category,
}: {
    isOpen: boolean;
    onClose: () => void;
    onEdit: (categoryId: number, name: string, color: StarColor) => void;
    category: ScrapCategory | null;
}) {
    const [name, setName] = useState("");
    const [selectedColor, setSelectedColor] = useState<StarColor>("red");

    useEffect(() => {
        if (category) {
            setName(category.name);
            setSelectedColor(category.starColor);
        }
    }, [category]);

    const handleEdit = () => {
        if (!name.trim() || !category) return;
        onEdit(category.categoryId, name.trim(), selectedColor);
        onClose();
    };

    return (
        <Modal isOpen={isOpen} onClose={onClose} size="sm">
            <div className="flex flex-col gap-5">
                <h2 className="text-[16px] font-bold text-gray-900">스크랩명</h2>

                <Input
                    placeholder="스크랩명을 입력하세요"
                    value={name}
                    onChange={(e) => setName((e.target as HTMLInputElement).value)}
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
                        onClick={onClose}
                        className="h-[48px] rounded-xl! text-gray-700!"
                    >
                        취소
                    </Button>
                    <Button
                        variant="primary"
                        size="full"
                        onClick={handleEdit}
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
// 카테고리 삭제 확인 모달
// ─────────────────────────────────────────────────────────
function DeleteConfirmModal({
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
            <div className="flex flex-col items-center gap-6 py-6 border-b-0!">
                <p className="text-[15px] font-medium text-gray-800 text-center">
                    해당 카테고리를 삭제하시겠습니까?
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
// 메인 스크랩 페이지
// ─────────────────────────────────────────────────────────
export default function ScrapsPage() {
    const router = useRouter();
    const [categories, setCategories] = useState<ScrapCategory[]>(MOCK_CATEGORIES);
    const [isNewCategoryOpen, setIsNewCategoryOpen] = useState(false);
    const [isMenuOpen, setIsMenuOpen] = useState(false);
    const [mode, setMode] = useState<'default' | 'edit' | 'delete'>('default');
    const [editingCategory, setEditingCategory] = useState<ScrapCategory | null>(null);
    const [deletingCategory, setDeletingCategory] = useState<ScrapCategory | null>(null);

    // 모든 스크랩 썸네일 모아서 표시
    const allThumbnails = categories.flatMap((cat) => cat.thumbnails);

    const handleAddCategory = (name: string, color: StarColor) => {
        const newCategory: ScrapCategory = {
            categoryId: Date.now(),
            name,
            starColor: color,
            thumbnails: [],
        };
        setCategories((prev) => [...prev, newCategory]);
    };

    const handleDeleteCategory = (categoryId: number) => {
        setCategories((prev) => prev.filter((c) => c.categoryId !== categoryId));
        setDeletingCategory(null);
    };

    const handleEditCategory = (categoryId: number, name: string, color: StarColor) => {
        setCategories((prev) =>
            prev.map((c) => (c.categoryId === categoryId ? { ...c, name, starColor: color } : c))
        );
    };

    return (
        <div className="flex flex-col min-h-full bg-bg_white font-pretendard overflow-x-hidden">

            {/* ── 헤더 ── */}
            <div className="relative">
                <Header
                    centerContent="스크랩"
                    rightContent={
                        mode !== 'default' ? (
                            <button
                                type="button"
                                onClick={() => setMode('default')}
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

                {/* 케밥 메뉴 드롭다운 */}
                {isMenuOpen && mode === 'default' && (
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
                                        setMode('edit');
                                        setIsMenuOpen(false);
                                    }}
                                    className="w-full text-center px-4 py-3 text-[14px] font-medium text-gray-800 transition-colors active:bg-gray-50 border-b border-gray-100"
                                >
                                    카테고리 수정
                                </button>
                                <button
                                    type="button"
                                    onClick={() => {
                                        setMode('delete');
                                        setIsMenuOpen(false);
                                    }}
                                    className="w-full text-center px-4 py-3 text-[14px] font-medium text-[#ab353a] transition-colors active:bg-red-50"
                                >
                                    카테고리 삭제
                                </button>
                            </div>
                        </div>
                    </>
                )}
            </div>

            {/* ── 콘텐츠 (2열 그리드) ── */}
            <div className="px-8 pt-5 pb-24">
                <div className="grid grid-cols-2 gap-6">

                    {/* 1. 새로운 카테고리 카드 */}
                    <button
                        type="button"
                        onClick={() => {
                            if (mode === 'default') setIsNewCategoryOpen(true);
                        }}
                        className={`flex flex-col items-center gap-2 cursor-pointer group ${mode !== 'default' ? 'pointer-events-none' : ''}`}
                    >
                        <div className="w-full aspect-square rounded-[20px] bg-white shadow-[0_2px_8px_rgba(0,0,0,0.08)] flex items-center justify-center">
                            <Plus size={44} className="text-[#333333] group-active:text-gray-500 transition-colors" strokeWidth={1.5} />
                        </div>
                        <span className="text-[13px] font-medium text-gray-600">새로운 카테고리</span>
                    </button>

                    {/* 2. 모든 스크랩 카드 */}
                    <div className={`flex flex-col items-center gap-2 cursor-pointer transition-opacity ${mode === 'default' ? 'active:opacity-80' : 'pointer-events-none'}`}>
                        <div className="relative w-full">
                            <ThumbnailGrid thumbnails={allThumbnails} />
                        </div>
                        <span className="text-[13px] font-medium text-gray-700">모든 스크랩</span>
                    </div>

                    {/* 3. 개별 카테고리 카드들 */}
                    {categories.map((category) => (
                        <div
                            key={category.categoryId}
                            onClick={() => {
                                if (mode === 'edit') {
                                    setEditingCategory(category);
                                } else if (mode === 'delete') {
                                    setDeletingCategory(category);
                                } else {
                                    router.push(`/scraps/${category.categoryId}`);
                                }
                            }}
                            className={`flex flex-col items-center gap-2 cursor-pointer transition-opacity ${mode === 'default' ? 'active:opacity-80' : ''}`}
                        >
                            <div className="relative w-full">
                                <ThumbnailGrid thumbnails={category.thumbnails} />
                                {/* 별 아이콘 (우측 상단) */}
                                <div className="absolute top-2 right-2">
                                    <Star
                                        size={20}
                                        fill={STAR_COLOR_MAP[category.starColor]}
                                        className="drop-shadow-sm"
                                        style={{ color: STAR_COLOR_MAP[category.starColor] }}
                                    />
                                </div>
                                {/* 모드에 따른 오버레이 효과 */}
                                {mode !== 'default' && (
                                    <div className="absolute inset-0 bg-white/60 rounded-[20px] flex items-center justify-center">
                                        {mode === 'edit' && (
                                            <Pencil size={40} className="text-gray-800 drop-shadow-md" strokeWidth={1.5} />
                                        )}
                                        {mode === 'delete' && (
                                            <Trash2 size={40} className="text-[#ab353a] drop-shadow-md" strokeWidth={1.5} />
                                        )}
                                    </div>
                                )}
                            </div>
                            <span className="text-[13px] font-medium text-gray-700">{category.name}</span>
                        </div>
                    ))}
                </div>
            </div>

            {/* ── 모달 ── */}
            <NewCategoryModal
                isOpen={isNewCategoryOpen}
                onClose={() => setIsNewCategoryOpen(false)}
                onAdd={handleAddCategory}
            />

            <EditCategoryModal
                isOpen={!!editingCategory}
                onClose={() => setEditingCategory(null)}
                onEdit={handleEditCategory}
                category={editingCategory}
            />

            <DeleteConfirmModal
                isOpen={!!deletingCategory}
                onClose={() => setDeletingCategory(null)}
                onDelete={() => {
                    if (deletingCategory) {
                        handleDeleteCategory(deletingCategory.categoryId);
                    }
                }}
            />
        </div>
    );
}
