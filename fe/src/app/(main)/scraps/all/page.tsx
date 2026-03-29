'use client';

import { useState, useEffect } from "react";
import Image from "next/image";
import { useRouter } from "next/navigation";
import { MapPin } from "lucide-react";
import Header from "@/common/components/Header";
import { ScrapCafeItem } from "@/features/scraps/types";
import { getAllScraps } from "@/features/scraps/api/scrapApi";
import { getImageUrl } from "@/common/utils/image";

// ─────────────────────────────────────────────────────────
// 카페 아이템 카드 (읽기 전용)
// ─────────────────────────────────────────────────────────
function ScrapCafeCard({
    cafe,
    onClick,
}: {
    cafe: ScrapCafeItem;
    onClick: () => void;
}) {
    return (
        <div
            onClick={onClick}
            className="flex items-center gap-4 bg-white rounded-2xl p-4 border border-gray-100 shadow-sm active:bg-gray-50 transition-colors cursor-pointer"
        >
            {/* 썸네일 */}
            <div className="relative w-[76px] h-[76px] shrink-0 rounded-xl overflow-hidden bg-[#F5F0E8]">
                {cafe.thumbnailUrl && (
                    <Image
                        src={getImageUrl(cafe.thumbnailUrl)}
                        alt={cafe.name}
                        fill
                        className="object-cover"
                        unoptimized
                    />
                )}
            </div>

            {/* 텍스트 영역 */}
            <div className="flex flex-col flex-1 min-w-0 justify-center gap-1">
                <h3 className="font-bold text-[14px] text-gray-900 truncate">{cafe.name}</h3>
                <p className="text-[12px] text-gray-500 truncate">{cafe.cafeIntro}</p>
                <div className="flex items-center gap-1 text-gray-400 mt-0.5">
                    <MapPin size={12} className="shrink-0" />
                    <span className="text-[12px] truncate">{cafe.address}</span>
                </div>
            </div>
        </div>
    );
}

// ─────────────────────────────────────────────────────────
// 기본 스크랩 (모든 스크랩) 페이지
// ─────────────────────────────────────────────────────────
export default function AllScrapsPage() {
    const router = useRouter();
    const [cafes, setCafes] = useState<ScrapCafeItem[]>([]);

    useEffect(() => {
        getAllScraps()
            .then((data) => {
                // cafeId 기준으로 중복 제거
                const unique = Array.from(
                    new Map(data.cafes.map((cafe) => [cafe.cafeId, cafe])).values()
                );
                setCafes(unique);
            })
            .catch((err) => console.error("전체 스크랩 조회 실패:", err));
    }, []);

    return (
        <div className="flex flex-col min-h-full bg-bg_white font-pretendard overflow-x-hidden">

            {/* ── 헤더 ── */}
            <Header
                leftContent="back"
                centerContent="기본 스크랩"
            />

            {/* ── 카페 리스트 ── */}
            <div className="flex flex-col gap-3 px-5 pt-4 pb-24">
                {cafes.length > 0 ? (
                    cafes.map((cafe) => (
                        <ScrapCafeCard
                            key={cafe.cafeId}
                            cafe={cafe}
                            onClick={() => router.push(`/cafes/${cafe.cafeId}`)}
                        />
                    ))
                ) : (
                    <div className="flex flex-col items-center justify-center py-20 text-gray-400">
                        <p className="text-[14px]">스크랩된 카페가 없습니다.</p>
                    </div>
                )}
            </div>
        </div>
    );
}
