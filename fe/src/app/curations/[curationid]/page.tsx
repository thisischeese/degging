"use client";

import Image from "next/image";
import { useRouter, useParams } from "next/navigation";
import { MapPin } from "lucide-react";
import backIcon from "@/assets/icons/backIcon.png";

// =====================================================================
// [정적 데이터 영역]
// 나중에 텍스트와 이미지 경로, 카페 아이디(id), 주소를 이곳에서 자유롭게 수정하시면 됩니다.
// 이미지들은 public/images/curation/ 폴더 안에 넣어주세요.
// =====================================================================

interface CurationCafe {
  id: number;
  name: string;
  shortDescription: string;
  address: string;
  description1: string;
  imageSrc: string;
  description2: string;
  mapImageSrc: string;
  listImageSrc: string;
}

interface CurationTheme {
  themeId: string;
  heroImage: string;
  title: string;
  introTitle: string;
  introDescription: string;
  date: string;
  cafes: CurationCafe[];
}

const CURATION_DATA: Record<string, CurationTheme> = {
  "1": {
    themeId: "1",
    heroImage: "/images/curation/curation1.png", // 홈 화면 큐레이션 썸네일과 동일한 이미지
    title: "두툼하고 쫀득한\n마성의 두쫀쿠 단면 모음",
    introTitle: "한 입 베어 물면 멈출 수 없는\n두껍고 쫀득한 쿠키의 매력\n",
    introDescription: "스트레스 받는 날, 진한 아메리카노와 함께 먹는 두툼한 쿠키는 완벽한 위로가 된다. 겉은 바삭하고 속은 쫀득한, 일명 '두쫀쿠' 맛집 4곳을 엄선했다. 각기 다른 매력을 자랑하는 빈틈없는 쿠키 성지들을 지금 바로 만나보자.",
    date: "2026.03.25",
    cafes: [
      {
        id: 1, // 실제 이동할 카페 ID
        name: "1. 첫 번째 두쫀쿠 카페",
        shortDescription: "쫀득함의 정석을 보여주는 쿠키 맛집",
        address: "서울특별시 마포구 위치 입력",
        description1: "첫 번째로 소개할 곳은 쫀득한 식감의 정석을 보여주는 카페입니다. 매장에서 매일 아침 구워내는 쿠키 냄새가 발길을 사로잡습니다.",
        imageSrc: "/images/curation/cafe1_1.png",
        description2: "특히 달콤한 초콜릿 청크가 듬뿍 들어간 시그니처 쿠키는 꼭 맛봐야 할 추천 메뉴입니다. 커피와 함께 곁들이면 완벽한 조합을 자랑하죠.",
        mapImageSrc: "/images/curation/map1_1.png",
        listImageSrc: "/images/curation/cafe1_1.png", // 리스트용 이미지 (동일한 이미지 활용 가능)
      },
      {
        id: 2,
        name: "2. 두 번째 두쫀쿠 카페",
        shortDescription: "다양한 크림치즈 필링이 들어간 쿠키",
        address: "서울특별시 서초구 위치 입력",
        description1: "두 번째 카페는 쿠키 안에 듬뿍 들어간 크림치즈 필링으로 유명한 곳입니다. 한 입 베어 물면 풍부한 치즈의 풍미가 입안 가득 퍼집니다.",
        imageSrc: "/images/curation/cafe1_2.png",
        description2: "황치즈, 로투스, 오레오 등 다채로운 라인업이 준비되어 있어 취향에 맞게 골라 먹는 재미가 쏠쏠합니다.",
        mapImageSrc: "/images/curation/map1_2.png",
        listImageSrc: "/images/curation/cafe1_2.png",
      },
      {
        id: 3,
        name: "3. 세 번째 두쫀쿠 카페",
        shortDescription: "황치즈 매니아들의 성지 쿠키",
        address: "서울특별시 강남구 위치 입력",
        description1: "세 번째는 황치즈 쿠키로 SNS를 뜨겁게 달군 맛집입니다. 단짠단짠의 조화가 시그니처인 이곳의 쿠키는 늦게 가면 품절되기 일쑤죠.",
        imageSrc: "/images/curation/cafe1_3.png",
        description2: "꾸덕한 텍스처와 진한 치즈 향을 좋아하는 분들에게 강력하게 추천하는 장소입니다.",
        mapImageSrc: "/images/curation/map1_3.png",
        listImageSrc: "/images/curation/cafe1_3.png",
      },
      {
        id: 4,
        name: "4. 네 번째 두쫀쿠 카페",
        shortDescription: "견과류가 듬뿍 들어간 고소한 쿠키",
        address: "서울특별시 용산구 위치 입력",
        description1: "마지막으로 소개할 곳은 고소한 견과류와 마카다미아가 통째로 들어간 프리미엄 쿠키 전문점입니다.",
        imageSrc: "/images/curation/cafe1_4.png",
        description2: "아낌없이 재료를 넣어 식감이 뛰어나며, 너무 달지 않아 누구나 부담 없이 담백하게 즐길 수 있습니다.",
        mapImageSrc: "/images/curation/map1_4.png",
        listImageSrc: "/images/curation/cafe1_4.png",
      }
    ]
  },
  "2": {
    themeId: "2",
    heroImage: "/images/curation/curation2.png",
    title: "겉바속촉 고소함의 끝\n인생 소금빵 모음",
    introTitle: "버터의 풍미와 짭짤함의 완벽한 밸런스\n놓치지 말아야 할 소금빵 맛집\n",
    introDescription: "담백하면서도 짭조름한 매력으로 꾸준한 인기를 끌고 있는 소금빵. 버터 홀이 뻥 뚫려있는 부드러운 식감부터 겉이 바삭한 바게트 스타일까지, 서울에서 꼽히는 인생 소금빵 맛집 4곳을 모았다.",
    date: "2026.03.25",
    cafes: [
      {
        id: 5,
        name: "1. 첫 번째 소금빵 카페",
        shortDescription: "바삭한 크러스트와 촉촉한 버터홀",
        address: "서울특별시 성동구 위치 입력",
        description1: "첫 번째 맛집은 굵은 소금이 콕콕 박혀 비주얼부터 시선을 사로잡는 곳입니다. 파삭하게 부서지는 겉면이 특징이죠.",
        imageSrc: "/images/curation/cafe2_1.png",
        description2: "속은 부드럽고 촉촉해 매일 먹어도 질리지 않는 기본에 가장 충실하면서 뛰어난 맛을 보여줍니다.",
        mapImageSrc: "/images/curation/map2_1.png",
        listImageSrc: "/images/curation/cafe2_1.png",
      },
      {
        id: 6,
        name: "2. 두 번째 소금빵 카페",
        shortDescription: "프리미엄 버터로 풍미를 극대화",
        address: "서울특별시 용산구 위치 입력",
        description1: "프랑스 고급 버터를 사용해 첫입부터 남다른 버터 풍미를 자랑하는 핫플레이스입니다.",
        imageSrc: "/images/curation/cafe2_2.png",
        description2: "갓 구워져 나왔을 때의 버터 향기 하나만으로도 오픈런을 감수할 만한 가치가 충분한 곳입니다.",
        mapImageSrc: "/images/curation/map2_2.png",
        listImageSrc: "/images/curation/cafe2_2.png",
      },
      {
        id: 7,
        name: "3. 세 번째 소금빵 카페",
        shortDescription: "크랙 소금빵의 정석, 겉바속촉 끝판왕",
        address: "서울특별시 종로구 위치 입력",
        description1: "마치 바게트처럼 질깃하고 바삭하게 씹히는 크랙 소금빵을 찾는다면 바로 이곳이 정답입니다.",
        imageSrc: "/images/curation/cafe2_3.png",
        description2: "묵직한 식감 사이로 녹아든 버터의 짭짤한 조화가 환상적이라 커피와의 페어링이 무척 훌륭합니다.",
        mapImageSrc: "/images/curation/map2_3.png",
        listImageSrc: "/images/curation/cafe2_3.png",
      },
      {
        id: 8,
        name: "4. 네 번째 소금빵 카페",
        shortDescription: "명란, 초코 등 다양한 퓨전 소금빵",
        address: "서울특별시 마포구 위치 입력",
        description1: "기본 소금빵도 맛있지만 우유크림, 명란, 초코 등 다양한 베리에이션 소금빵으로 유명한 카페입니다.",
        imageSrc: "/images/curation/cafe2_4.png",
        description2: "트렌디한 입맛을 저격하는 화려한 비주얼과 속재료 덕분에 포장해 가는 손님들로 항상 붐빕니다.",
        mapImageSrc: "/images/curation/map2_4.png",
        listImageSrc: "/images/curation/cafe2_4.png",
      }
    ]
  },
  "3": {
    themeId: "3",
    heroImage: "/images/curation/curation3.png",
    title: "쌉싸름한 녹색의 유혹\n입맛 돋우는 말차 디저트",
    introTitle: "진한 잎차의 풍미를 그대로 담은\n말차 덕후들의 필수 코스\n",
    introDescription: "달콤함 끝에 밀려오는 은은하고 고급스러운 쌉싸름함. 쫀득한 갸또 케이크부터 꾸덕한 말차 테린느, 시원한 아이스크림 라떼까지. 깊고 진한 색감만큼이나 농밀한 맛을 자랑하는 찐 말차 디저트 성지 4곳을 소개한다.",
    date: "2026.03.25",
    cafes: [
      {
        id: 9,
        name: "1. 첫 번째 말차 카페",
        shortDescription: "제주산 프리미엄 유기농 말차 갸또",
        address: "서울특별시 마포구 위치 입력",
        description1: "가장 좋은 등급의 제주 말차를 사용하여 텁텁함 없이 깔끔하고 진한 향을 맛볼 수 있는 카페입니다.",
        imageSrc: "/images/curation/cafe3_1.png",
        description2: "부드럽게 흘러내리는 말차 크림 시그니처 라떼와 꾸덕한 식감이 살아있는 갸또 케이크가 이곳의 투톱 메뉴입니다.",
        mapImageSrc: "/images/curation/map3_1.png",
        listImageSrc: "/images/curation/cafe3_1.png",
      },
      {
        id: 10,
        name: "2. 두 번째 말차 카페",
        shortDescription: "생초콜릿처럼 꾸덕한 말차 테린느",
        address: "서울특별시 강남구 위치 입력",
        description1: "입에 넣자마자 녹아내리는 극강의 꾸덕함. 밀가루를 최소화하고 말차와 초콜릿으로 꽉 채운 테린느 맛집입니다.",
        imageSrc: "/images/curation/cafe3_2.png",
        description2: "진한 커피 한 모금과 곁들이면 말차 본연의 깊은 쌉싸름함과 은은한 단맛의 마법을 경험할 수 있습니다.",
        mapImageSrc: "/images/curation/map3_2.png",
        listImageSrc: "/images/curation/cafe3_2.png",
      },
      {
        id: 11,
        name: "3. 세 번째 말차 카페",
        shortDescription: "풍성한 말차 크림이 올라간 아인슈페너",
        address: "서울특별시 서대문구 위치 입력",
        description1: "에스프레소 베이스에 아주 밀도 높은 말차 크림을 듬뿍 얹어주는 말차 아인슈페너 전문 로스터리입니다.",
        imageSrc: "/images/curation/cafe3_3.png",
        description2: "입을 대고 마셨을 때 가장 먼저 느껴지는 크림의 달콤쌉쌀함과 이어지는 커피의 밸런스가 기가 막힙니다.",
        mapImageSrc: "/images/curation/map3_3.png",
        listImageSrc: "/images/curation/cafe3_3.png",
      },
      {
        id: 12,
        name: "4. 네 번째 말차 카페",
        shortDescription: "바삭한 타르트지 위의 몽블랑 말차",
        address: "서울특별시 강남구 위치 입력",
        description1: "섬세하게 짠 말차 앙금으로 덮인 몽블랑 타르트로 시선을 사로잡은 고급스러운 디저트 숍입니다.",
        imageSrc: "/images/curation/cafe3_4.png",
        description2: "바삭한 타르트지와 부드러운 샹티 크림, 그리고 쌉쌀한 말차의 3박자가 입안에서 황홀하게 어우러집니다.",
        mapImageSrc: "/images/curation/map3_4.png",
        listImageSrc: "/images/curation/cafe3_4.png",
      }
    ]
  },
  "4": {
    themeId: "4",
    heroImage: "/images/curation/curation4.png",
    title: "상큼 달콤한 과일의 제왕\n프리미엄 딸기 케이크",
    introTitle: "입안 가득 번지는 싱그러운 맛\n실패 없는 딸기 케이크 대전\n",
    introDescription: "스폰지케이크 사이사이 생딸기가 듬뿍 박힌 쇼트케이크부터 묵직한 타르트, 달콤한 프레지에까지. 새빨간 비주얼에 한 번, 달콤한 생크림과의 조화에 두 번 반하게 되는 서울 최고의 딸기 디저트 카페 4곳을 소개한다.",
    date: "2026.03.25",
    cafes: [
      {
        id: 13,
        name: "1. 첫 번째 딸기 케이크 카페",
        shortDescription: "100% 동물성 생크림 딸기 쇼트케이크",
        address: "서울특별시 마포구 위치 입력",
        description1: "새하얀 100% 동물성 우유 생크림과 당도 높은 설향 딸기만을 고집하는 정통 쇼트케이크 전문점입니다.",
        imageSrc: "/images/curation/cafe4_1.png",
        description2: "시트마저 입안에서 눈처럼 사르르 녹아내려, 홀케이크 한 판도 순식간에 비우게 되는 최고의 딸기 케이크를 자랑합니다.",
        mapImageSrc: "/images/curation/map4_1.png",
        listImageSrc: "/images/curation/cafe4_1.png",
      },
      {
        id: 14,
        name: "2. 두 번째 딸기 케이크 카페",
        shortDescription: "프랑스식 프리미엄 디저트 프레지에",
        address: "서울특별시 서초구 위치 입력",
        description1: "바닐라빈이 콕콕 박힌 묵직한 무슬린 크림과 신선한 딸기의 단면이 아름답게 장식된 프레지에 맛집입니다.",
        imageSrc: "/images/curation/cafe4_2.png",
        description2: "크림의 리치함과 딸기 과즙이 터지면서 만들어내는 깊고 고급스러운 하모니가 일품입니다.",
        mapImageSrc: "/images/curation/map4_2.png",
        listImageSrc: "/images/curation/cafe4_2.png",
      },
      {
        id: 15,
        name: "3. 세 번째 딸기 케이크 카페",
        shortDescription: "통나무 모양의 거대한 왕딸기 롤케이크",
        address: "서울특별시 송파구 위치 입력",
        description1: "초크초크한 수플레 시트 안에 주먹만한 킹스베리 딸기가 통째로 밀어 넣어 돌돌 말아낸 시그니처 롤케이크가 유명합니다.",
        imageSrc: "/images/curation/cafe4_3.png",
        description2: "포크로 쫀득한 크림과 시트, 생과일을 듬뿍 떠서 한 번에 먹었을 때 상큼달콤함의 진가를 느낄 수 있습니다.",
        mapImageSrc: "/images/curation/map4_3.png",
        listImageSrc: "/images/curation/cafe4_3.png",
      },
      {
        id: 16,
        name: "4. 네 번째 딸기 케이크 카페",
        shortDescription: "크림치즈 다이빙! 베리 듬뿍 타르트",
        address: "서울특별시 용산구 위치 입력",
        description1: "아몬드 크림 층을 깐 바삭한 타르트지 위에 진한 크림치즈와 생딸기를 산처럼 쌓아 올린 비주얼 깡패 디저트 숍입니다.",
        imageSrc: "/images/curation/cafe4_4.png",
        description2: "꾸덕한 크림치즈의 눅진함과 과일의 새콤달콤함이 폭발적으로 어울려 특별한 날 선물용으로도 베스트셀러입니다.",
        mapImageSrc: "/images/curation/map4_4.png",
        listImageSrc: "/images/curation/cafe4_4.png",
      }
    ]
  }
};

export default function CurationDetailPage() {
  const router = useRouter();
  const params = useParams();
  
  // URL에서 curationid 파라미터 가져오기 (없으면 1번 큐레이션 기본값)
  const idParam = typeof params?.curationid === "string" ? params.curationid : "1";
  const curation = CURATION_DATA[idParam] || CURATION_DATA["1"];

  return (
    <div className="flex flex-col flex-1 overflow-y-auto no-scrollbar bg_white font-nanum">
      
      {/* --- 섹션 1: 메인 히어로 이미지 --- */}
      <section className="relative w-full h-[520px] shrink-0 overflow-hidden bg-gray-200">
        <Image 
          src={curation.heroImage} 
          alt="메인 이미지" 
          fill 
          sizes="(max-width: 768px) 100vw, 768px"
          className="object-cover" 
        />
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
            {curation.title.split('\n').map((line: string, idx: number) => (
              <span key={idx}>
                {line}
                <br />
              </span>
            ))}
          </h1>
        </div>
      </section>

      {/* --- 섹션 2: 인트로 --- */}
      <section className="px-8 pt-14">
        <p className="text-[#424242] text-[16px] leading-[1.8] break-keep font-nanum_bold mb-10">
          {curation.introTitle.split('\n').map((line: string, idx: number) => (
            <span key={idx}>
              {line}
              <br />
            </span>
          ))}
        </p>
        <p className="text-[14px] text-[#616161] leading-[2.5] break-keep font-nanum">
          {curation.introDescription}
        </p>
        {/* 커스텀 구분선 이미지 */}
        <div className="flex justify-center my-10">
            <div className="relative w-[150px] h-[60px]">
                <Image 
                  src="/images/curation/divideLine.png" 
                  alt="구분선" 
                  fill 
                  className="object-contain" 
                  sizes="150px"
                />
            </div>
        </div>
      </section>

      {/* --- 섹션 3: 카페 개별 소개 --- */}
      {curation.cafes.map((cafe: CurationCafe) => (
        <section key={cafe.id} className="px-8">
          <h2 className="text-[19px] font-nanum_bold mb-5">{cafe.name}</h2>
          <p className="text-[14px] text-[#616161] leading-[2.5] break-keep font-nanum mb-8">
            {cafe.description1}
          </p>

          <div 
            className="w-full h-[180px] bg-[#F5F5F5] rounded-2xl mb-10 relative cursor-pointer overflow-hidden border border-gray-100"
            onClick={() => router.push(`/cafes/${cafe.id}`)}
          >
             {/* 카페 상세 이미지가 없을 경우를 대비해 Fallback 컬러 지정 */}
             <div className="absolute inset-0 flex items-center justify-center text-gray-400 text-[12px] bg-gray-100 z-0">
                [ {cafe.name} 이미지 영역 ]
             </div>
             <Image 
               src={cafe.imageSrc} 
               alt={`${cafe.name} 이미지`} 
               fill 
               className="object-cover z-10" 
               sizes="(max-width: 768px) 100vw, 768px"
             />
          </div>
          <p className="text-[14px] text-[#616161] leading-[2.5] break-keep font-nanum mb-8">
            {cafe.description2}
          </p>
          
          {/* 지도 정적 이미지 영역 */}
          <div 
            className="w-full h-[180px] bg-[#F5F5F5] rounded-2xl relative cursor-pointer overflow-hidden border border-gray-100"
            onClick={() => router.push(`/cafes/${cafe.id}`)}
          >
             <div className="absolute inset-0 flex items-center justify-center text-gray-400 text-[12px] bg-gray-100 z-0">
                [ 지도 API 이미지 영역 ]
             </div>
             <Image 
               src={cafe.mapImageSrc} 
               alt={`${cafe.name} 지도`} 
               fill 
               className="object-cover z-10" 
               sizes="(max-width: 768px) 100vw, 768px"
             />
          </div>
          
          {/* 커스텀 구분선 이미지 */}
          <div className="flex justify-center my-10">
            <div className="relative w-[150px] h-[60px]">
                <Image 
                  src="/images/curation/divideLine.png" 
                  alt="구분선" 
                  fill 
                  className="object-contain"
                  sizes="150px"
                />
            </div>
        </div>
        </section>
      ))}

      {/* --- 섹션 4: 카페 모음 리스트 --- */}
      <section className="px-8 pt-6 pb-14 bg-[#F7F7F5]">
        <h2 className="text-[18px] font-nanum_bold text-gray-900 mb-2">큐레이션에 포함된 맛집 모음</h2>
        <div className="flex flex-col font-pretendard">
          {curation.cafes.map((cafe: CurationCafe) => (
            <div 
              key={cafe.id}
              onClick={() => router.push(`/cafes/${cafe.id}`)}
              className="flex items-center gap-5 py-5 border-t border-[#D6DCE5] last:border-b cursor-pointer active:bg-black/5"
            >
              <div className="w-[72px] h-[72px] relative shrink-0 rounded-md overflow-hidden bg-gray-200">
                <Image 
                  src={cafe.listImageSrc} 
                  alt="카페" 
                  fill 
                  className="object-cover" 
                  sizes="72px"
                />
              </div>
              <div className="flex flex-col justify-center gap-1.5 flex-1">
                <span className="text-[16px] font-bold text-gray-900 line-clamp-1">{cafe.name}</span>
                <span className="text-[14px] text-gray-700 leading-none line-clamp-1">{cafe.shortDescription}</span>
                <span className="text-[13px] text-gray-500 flex items-center gap-1 leading-none mt-0.5 max-w-[95%]">
                  <MapPin className="w-3.5 h-3.5 shrink-0" />
                  <span className="truncate">{cafe.address}</span>
                </span>
              </div>
            </div>
          ))}
        </div>
        
        <div className="mt-2 pb-10">
          <p className="text-[12px] text-gray-500 font-nanum">작성 일자 {curation.date}</p>
        </div>
      </section>
    </div>
  );
}