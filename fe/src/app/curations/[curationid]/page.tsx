"use client";

import Image from "next/image";
import { useRouter } from "next/navigation";
import { MapPin } from "lucide-react";
import backIcon from "@/assets/icons/backIcon.png";

export default function CurationDetailPage() {
  const router = useRouter();

  const cafeList = [1, 2, 3, 4].map((id) => ({
    id,
    name: "리마인 망원 (REFINE)",
    description: "망원동에 위치한 캐주얼 다이닝",
    address: "서울특별시 마포구 망원동",
  }));

  return (
    <div className="flex flex-col flex-1 overflow-y-auto no-scrollbar bg_white font-nanum"> {/* 기본 폰트 나눔으로 변경 */}
      
      {/* --- 섹션 1: 메인 히어로 이미지 --- */}
      <section className="relative w-full h-[520px] shrink-0 overflow-hidden">
        <Image src="/images/curation/mangoBingsu.png" alt="메인 이미지" fill className="object-cover" />
        <div className="absolute inset-0 bg-black/25" />
        
        <button 
          onClick={() => router.back()}
          className="absolute top-6 left-6 w-8 h-8 flex items-center justify-center active:scale-95 transition-transform z-10"
        >
          <div className="absolute inset-0 bg-black/40 rounded-full" />
          <Image src={backIcon} alt="뒤로가기" className="relative w-8 h-8 brightness-0 invert object-contain" />
        </button>

        <div className="absolute bottom-12 px-8">
          <h1 className="text-white text-[30px] font-nanum_bold leading-tight drop-shadow-md">
            무더위 날려버릴<br />완벽한 당도의 망고 빙수
          </h1>
        </div>
      </section>

      {/* --- 섹션 2: 인트로 --- */}
      <section className="px-8 pt-14">
        <p className="text-[#424242] text-[16px] leading-[1.8] break-keep font-nanum_bold mb-10">
          한 입이면 여름이 녹는다.<br />
          달콤하고 시원한 망고의 계절<br />
        </p>
        <p className="text-[14px] text-[#616161] leading-[2.5] break-keep font-nanum">
          여름의 열기가 한창일 때, 가장 먼저 떠오르는 디저트가 있다. 바로 얼음 위에 달콤한 망고가 듬뿍 올라간 망고빙수다. 한 숟가락 떠먹는 순간, 시원한 우유 얼음과 과즙 가득한 망고의 달콤함이 입안에서 녹아내리며 무더위를 단번에 잊게 만든다. 오늘은 올여름, 더위를 시원하게 날려줄 완벽한 당도의 망고빙수를 큐레이팅해 소개한다.
        </p>
        {/* 커스텀 구분선 이미지 */}
        <div className="flex justify-center my-10">
            <div className="relative w-[150px] h-[60px]">
                <Image 
                src="/images/curation/divideLine.png" 
                alt="구분선" 
                fill 
                className="object-contain" 
                />
            </div>
        </div>
      </section>

      {/* --- 섹션 3: 카페 개별 소개 --- */}
      {[1, 2, 3, 4].map((item) => (
        <section key={item} className="px-8">
          <h2 className="text-[19px] font-nanum_bold mb-5">{item}. 당옥</h2>
          <p className="text-[14px] text-[#616161] leading-[2.5] break-keep font-nanum mb-8">
            신사역 8번 출구 근처에 있는 일본식 디저트 카페 당옥에 들르면, 여름에 특히 찾게 되는 메뉴가 바로 망고빙수입니다. 부드럽게 갈린 우유 얼음 위에 달콤하게 익은 망고를 넉넉하게 올려, 한 숟갈만 떠도 상큼한 과즙과 시원한 달콤함이 자연스럽게 퍼집니다.
          </p>

          <div 
            className="w-full h-[180px] bg-[#F5F5F5] rounded-2xl mb-10 relative cursor-pointer overflow-hidden"
            onClick={() => router.push(`/cafes/${item}`)}
          >
             <div className="absolute inset-0 flex items-center justify-center text-gray-400 text-[12px]">
                [ 디저트 이미지 영역 ]
             </div>
          </div>
          <p className="text-[14px] text-[#616161] leading-[2.5] break-keep font-nanum mb-8">
            신사역 8번 출구 근처에 있는 일본식 디저트 카페 당옥에 들르면, 여름에 특히 찾게 되는 메뉴가 바로 망고빙수입니다. 부드럽게 갈린 우유 얼음 위에 달콤하게 익은 망고를 넉넉하게 올려, 한 숟갈만 떠도 상큼한 과즙과 시원한 달콤함이 자연스럽게 퍼집니다.
          </p>
          
          {/* 지도 정적 이미지 영역 */}
          <div 
            className="w-full h-[180px] bg-[#F5F5F5] rounded-2xl relative cursor-pointer overflow-hidden"
            onClick={() => router.push(`/cafes/${item}`)}
          >
             <div className="absolute inset-0 flex items-center justify-center text-gray-400 text-[12px]">
                [ 지도 API 이미지 영역 ]
             </div>
          </div>
          
          {/* 커스텀 구분선 이미지 */}
          <div className="flex justify-center my-10">
            <div className="relative w-[150px] h-[60px]">
                <Image 
                src="/images/curation/divideLine.png" 
                alt="구분선" 
                fill 
                className="object-contain"
                />
            </div>
        </div>
        </section>
      ))}

      {/* --- 섹션 4: 카페 모음 리스트 (여기서부터 배경색 변경) --- */}
      <section className="px-8 pt-6 pb-14 bg-[#F7F7F5]">
        <h2 className="text-[18px] font-nanum_bold text-gray-900 mb-2">큐레이션에 포함된 카페 모음</h2>
        <div className="flex flex-col font-pretendard">
          {cafeList.map((cafe) => (
            <div 
              key={cafe.id}
              onClick={() => router.push(`/cafes/${cafe.id}`)}
              className="flex items-center gap-5 py-5 border-t border-[#D6DCE5] last:border-b cursor-pointer active:bg-black/5"
            >
              <div className="w-[72px] h-[72px] relative shrink-0">
                <Image src="/images/curation/mangoBingsu.png" alt="카페" fill className="object-cover" />
              </div>
              <div className="flex flex-col justify-center gap-1.5">
                <span className="text-[16px] font-bold text-gray-900">{cafe.name}</span>
                <span className="text-[14px] text-gray-700 leading-none">{cafe.description}</span>
                <span className="text-[13px] text-gray-500 flex items-center gap-1 leading-none mt-0.5">
                  <MapPin className="w-3.5 h-3.5" />
                  {cafe.address}
                </span>
              </div>
            </div>
          ))}
        </div>
        
        <div className="mt-2 pb-10">
          <p className="text-[12px] text-gray-500 font-nanum">작성 일자 2026.03.06</p>
        </div>
      </section>
    </div>
  );
}