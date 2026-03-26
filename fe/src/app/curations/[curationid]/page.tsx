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
  objectPosition?: string;
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
    heroImage: "/images/curation/duzzonku.jpg", // 홈 화면 큐레이션 썸네일과 동일한 이미지
    title: "두툼하고 쫀득한\n마성의 두쫀쿠 단면 모음",
    introTitle: "한 입 베어 물면 멈출 수 없는\n두껍고 쫀득한 쿠키의 매력\n",
    introDescription: "스트레스 받는 날, 진한 아메리카노와 함께 먹는 두툼한 쿠키는 완벽한 위로가 된다. 겉은 바삭하고 속은 쫀득한, 일명 '두쫀쿠' 맛집 4곳을 엄선했다. 각기 다른 매력을 자랑하는 빈틈없는 쿠키 성지들을 지금 바로 만나보자.",
    date: "2026.03.25",
    cafes: [
      {
        id: 1,
        name: "1. 카페구움",
        shortDescription: "묵직한 위로가 필요한 날, 두께감부터 남다른 정석의 맛",
        address: "서울 강남구 논현로 520 청송빌딩 1층 101호",
        description1: "스트레스가 턱끝까지 차오른 날, 매장 문을 열자마자 풍기는 진한 버터 향기가 마음을 어루만진다. 투박하지만 한 손에 꽉 차는 두툼한 두께는 보는 것만으로도 든든한 위로가 된다.",
        imageSrc: "/images/curation/duzzonku1.jpg",
        description2: "반으로 가르면 꾸덕하게 늘어나는 밀도 높은 반죽이 '두쫀쿠'의 정석을 보여준다. 큼지막하게 박힌 초콜릿 청크가 오독오독 씹히며, 진득한 쫀득함과 어우러져 완벽한 식감을 선사한다.",
        mapImageSrc: "/images/curation/duzzonku_map1.png",
        listImageSrc: "/images/curation/duzzonku1.jpg", // 리스트용 이미지 (동일한 이미지 활용 가능)
      },
      {
        id: 2,
        name: "2. 커피스피릿",
        shortDescription: "다양한 크림치즈 필링이 들어간 쿠키",
        address: "서울 노원구 공릉로37길 13 1층",
        description1: "두 번째 카페는 쿠키 안에 듬뿍 들어간 크림치즈 필링으로 유명한 곳입니다. 한 입 베어 물면 풍부한 치즈의 풍미가 입안 가득 퍼집니다.",
        imageSrc: "/images/curation/duzzonku2.jpg",
        description2: "황치즈, 로투스, 오레오 등 다채로운 라인업이 준비되어 있어 취향에 맞게 골라 먹는 재미가 쏠쏠합니다.",
        mapImageSrc: "/images/curation/duzzonku_map2.png",
        listImageSrc: "/images/curation/duzzonku2.jpg",
      },
      {
        id: 3,
        name: "3. 카페 두댓",
        shortDescription: "황치즈 매니아들의 성지 쿠키",
        address: "서울 강남구 논현로 520 청송빌딩 1층 101호",
        description1: "세 번째는 강남 두쫀쿠 강자입니다. 적절한 단맛과 쫀득함의 조화가 시그니처인 이곳의 쿠키는 늦게 가면 품절되기 일쑤죠.",
        imageSrc: "/images/curation/duzzonku3.png",
        description2: "진짜 두쫀쿠를 경험하고 싶은 분들에게 강력하게 추천하는 장소입니다.",
        mapImageSrc: "/images/curation/duzzonku_map3.png",
        listImageSrc: "/images/curation/duzzonku3.png",
        objectPosition: "center 38%",
      },
      {
        id: 4,
        name: "4. 낫배드커피 한남",
        shortDescription: "견과류가 듬뿍 들어간 고소한 쿠키",
        address: "서울 용산구 이태원로49길 37",
        description1: "마지막으로 소개할 곳은 고소한 견과류와 마카다미아가 통째로 들어간 프리미엄 쿠키 전문점입니다.",
        imageSrc: "/images/curation/duzzonku4.jpg",
        description2: "아낌없이 재료를 넣어식감이 뛰어나며, 너무 달지 않아 누구나 부담 없이 담백하게 즐길 수 있습니다.",
        mapImageSrc: "/images/curation/duzzonku_map4.png",
        listImageSrc: "/images/curation/duzzonku4.jpg",
      }
    ]
  },
  "2": {
    themeId: "2",
    heroImage: "/images/curation/soguem.jpg",
    title: "겉바속촉 고소함의 끝\n인생 소금빵 모음",
    introTitle: "버터의 풍미와 짭짤함의 완벽한 밸런스\n놓치지 말아야 할 소금빵 맛집\n",
    introDescription: "담백하면서도 짭조름한 매력으로 꾸준한 인기를 끌고 있는 소금빵. 버터 홀이 뻥 뚫려있는 부드러운 식감부터 겉이 바삭한 바게트 스타일까지, 서울에서 꼽히는 인생 소금빵 맛집 4곳을 모았다.",
    date: "2026.03.25",
    cafes: [
      {
        id: 5,
        name: "1. 아티스트베이커리 안국",
        shortDescription: "파삭한 크러스트와 쫄깃한 결이 빚어낸 소금빵의 정석",
        address: "서울 종로구 율곡로 45 1층",
        description1: "소금빵의 생명인 '겉바속촉'의 대비를 가장 훌륭하게 구현해 낸 곳이다. 굵은 소금이 얹혀진 겉면은 기분 좋게 파삭하고, 반으로 가르면 촉촉하게 숨어있던 버터 동굴이 모습을 드러낸다.",
        imageSrc: "/images/curation/soguem1.jpg",
        description2: "팬에 눌어붙어 구워진 밑면의 바삭함과 결대로 찢어지는 부드러운 속살이 입안에서 완벽한 조화를 이룬다. 기본기에 얼마나 충실했는지 한 입만으로도 고스란히 전해진다.",
        mapImageSrc: "/images/curation/soguem_map1.png",
        listImageSrc: "/images/curation/soguem1.jpg",
      },
      {
        id: 6,
        name: "2. 오소리 베이커리 어린이대공원",
        shortDescription: "부드러운 빵결 사이로 스며든 프랑스 버터의 깊은 풍미",
        address: "서울 광진구 능동로 177 1-3층",
        description1: "최고급 프랑스 버터를 아낌없이 넣어, 빵을 굽는 시간마다 골목 전체에 농밀한 향기가 피어오른다. 첫입부터 마지막 입까지 버터의 짙은 풍미가 입안을 가득 채우는 소금빵이다.",
        imageSrc: "/images/curation/soguem2.jpg",
        description2: "입술에 묻어나는 부드러운 버터의 질감과 짭조름한 소금의 조화는 단순하지만 가장 깊은 여운을 남긴다. 따뜻하게 데워 먹으면 갓 구워낸 듯한 식감과 향을 온전히 느낄 수 있다.",
        mapImageSrc: "/images/curation/soguem_map2.png",
        listImageSrc: "/images/curation/soguem2.jpg",
      },
      {
        id: 7,
        name: "3. 서울소금빵",
        shortDescription: "질깃하고 단단한 매력, 입안에서 부서지는 크랙 소금빵",
        address: "서울 중구 다산로20길 32 1층",
        description1: "부드럽고 푹신한 모닝빵 스타일의 소금빵에 익숙해졌다면, 거칠고 매력적인 크랙 소금빵의 세계를 경험해 볼 차례다. 바게트처럼 단단하고 질깃한 식감이 씹는 즐거움을 선사한다.",
        imageSrc: "/images/curation/soguem3.jpg",
        description2: "묵직하게 씹히는 빵결 사이로 스며든 짭짤함은 진한 커피와 페어링했을 때 비로소 완성된다. 천천히 씹을수록 밀가루의 구수함과 버터의 향이 올라와 자꾸만 손이 간다.",
        mapImageSrc: "/images/curation/soguem_map3.png",
        listImageSrc: "/images/curation/soguem3.jpg",
      },
      {
        id: 8,
        name: "4. 베통 성수",
        shortDescription: "독특한 모양새 속에 꽉 찬 쫄깃함, 다채로운 퓨전 소금빵",
        address: "서울 성동구 연무장7가길 8",
        description1: "익숙한 초승달 모양을 탈피한 특유의 통통한 비주얼로 시선을 끈다. 소금빵을 캔버스 삼아 명란, 우유크림 등 다양한 속재료를 채워 넣어 다채로운 미식의 세계를 그려낸다.",
        imageSrc: "/images/curation/soguem4.jpg",
        description2: "화려한 변주 속에서도 결코 잃지 않은 것은 소금빵 본연의 쫄깃한 식감이다. 떡처럼 찰기 있는 반죽과 짭짤한 겉면이 어떤 재료와 만나도 훌륭한 균형을 유지한다.",
        mapImageSrc: "/images/curation/soguem_map4.png",
        listImageSrc: "/images/curation/soguem4.jpg",
        objectPosition: "center 35%",
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
        name: "1. 틸데",
        shortDescription: "제주 말차의 깊은 쌉싸름함을 오롯이 품은 꾸덕한 갸또",
        address: "서울특별시 마포구 위치 입력",
        description1: "텁텁함 없이 맑고 깊은 쌉싸름함. 최상급 제주 유기농 찻잎을 사용해 빚어낸 말차 갸또는 차분하고 우아한 색감만큼이나 정갈한 맛을 낸다.",
        imageSrc: "/images/curation/cafe3_1.png",
        description2: "포크 자국이 선명하게 남을 만큼 밀도 높은 꾸덕함을 자랑한다. 케이크 한 조각을 천천히 음미하다 보면, 달콤함 끝에 밀려오는 짙은 녹차 향이 복잡했던 마음마저 차분하게 가라앉힌다.",
        mapImageSrc: "/images/curation/map3_1.png",
        listImageSrc: "/images/curation/cafe3_1.png",
      },
      {
        id: 10,
        name: "2. 크림커넥션 이태원점",
        shortDescription: "밀가루 없이 말차의 농밀함만으로 꽉 채워낸 테린느",
        address: "서울특별시 강남구 위치 입력",
        description1: "말차를 향한 진심을 한 조각에 옹골차게 압축했다. 밀가루를 배제하고 질 좋은 말차와 초콜릿으로만 굳혀낸 테린느는 디저트라기보다 고급 생초콜릿을 씹는 듯한 감각을 선사한다.",
        imageSrc: "/images/curation/cafe3_2.png",
        description2: "혀끝에 닿는 순간 체온에 의해 천천히, 그리고 진득하게 녹아내리는 텍스처가 매력적이다. 말차 특유의 비릿함 없이 깔끔하고 농밀한 향만이 입안에 깊게 머문다.",
        mapImageSrc: "/images/curation/map3_2.png",
        listImageSrc: "/images/curation/cafe3_2.png",
      },
      {
        id: 11,
        name: "3. 가배도 시청점",
        shortDescription: "진한 에스프레소 위로 내려앉은 쫀쫀한 말차 크림의 조화",
        address: "서울특별시 서대문구 위치 입력",
        description1: "말차의 풍미를 마시는 형태로 즐기고 싶은 이들에게 제격인 말차 아인슈페너. 짙은 에스프레소 위로 묵직하게 얹어진 녹색 말차 크림의 색감 대비가 무척 아름답다.",
        imageSrc: "/images/curation/cafe3_3.png",
        description2: "잔을 기울이면 차가운 말차 크림이 입술을 부드럽게 감싸고, 이내 쌉싸름한 커피가 틈새를 비집고 들어온다. 커피와 말차, 두 가지 깊은 향이 섞이지 않고 각자의 매력을 뽐낸다.",
        mapImageSrc: "/images/curation/map3_3.png",
        listImageSrc: "/images/curation/cafe3_3.png",
      },
      {
        id: 12,
        name: "4. 무브모브 카페/스튜디오",
        shortDescription: "바삭한 타르트지 위로 섬세하게 피어난 말차 몽블랑",
        address: "서울특별시 강남구 위치 입력",
        description1: "한 땀 한 땀 정성스레 짜 올린 말차 앙금 실타래는 마치 하나의 예술 작품을 보는 듯하다. 화려한 몽블랑 비주얼 아래에는 입안을 즐겁게 할 다채로운 식감의 향연이 기다리고 있다.",
        imageSrc: "/images/curation/cafe3_4.png",
        description2: "경쾌하게 부서지는 타르트지와 가벼운 생크림, 그리고 묵직하고 쌉쌀한 말차 앙금이 입안에서 차례로 허물어진다. 말차가 품은 쌉싸름함을 가장 섬세하고 우아하게 풀어낸 디저트다.",
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
        name: "1. 1020룸",
        shortDescription: "순백의 동물성 생크림과 생딸기가 빚어낸 정통 쇼트케이크",
        address: "서울특별시 마포구 위치 입력",
        description1: "새하얀 눈밭에 붉은 꽃이 핀 듯 정갈한 딸기 쇼트케이크. 식물성 크림의 인위적인 맛을 배제하고, 순수 100% 동물성 생크림과 당도 높은 설향 딸기만을 사용해 정통의 맛을 구현했다.",
        imageSrc: "/images/curation/cafe4_1.png",
        description2: "입술에 닿자마자 눈송이처럼 사르르 녹아내리는 퐁신한 시트 사이로 생딸기 과즙이 팡 터져 나온다. 기분 좋은 우유의 고소함과 과일의 상큼함만이 입안에 깔끔하게 남는다.",
        mapImageSrc: "/images/curation/map4_1.png",
        listImageSrc: "/images/curation/cafe4_1.png",
      },
      {
        id: 14,
        name: "2. 미니마이즈 이태원점",
        shortDescription: "깊은 풍미의 바닐라 크림이 돋보이는 우아한 딸기 프레지에",
        address: "서울특별시 서초구 위치 입력",
        description1: "단면을 빼곡히 채운 붉은 딸기가 시각적인 만족감을 먼저 채워주는 프랑스식 프레지에 케이크다. 밀가루를 쓰지 않은 글루텐프리 시트를 더해 부대낌 없이 편안한 맛을 선사한다.",
        imageSrc: "/images/curation/cafe4_2.png",
        description2: "묵직하고 리치한 무슬린 크림 속에 콕콕 박힌 바닐라빈은 딸기의 싱그러운 산미를 한층 고급스럽게 감싸 안는다. 특별한 기념일, 분위기를 내고 싶은 날 가장 먼저 생각나는 한 조각이다.",
        mapImageSrc: "/images/curation/map4_2.png",
        listImageSrc: "/images/curation/cafe4_2.png",
      },
      {
        id: 15,
        name: "3. 위베이브베이크샵",
        shortDescription: "커다란 생딸기를 통째로 품어낸 압도적 굵기의 롤케이크",
        address: "서울특별시 송파구 위치 입력",
        description1: "일반적인 얇은 롤케이크를 상상했다면 오산이다. 큼지막한 생딸기들을 수플레 시트로 투박하면서도 먹음직스럽게 말아내어, 보기만 해도 마음이 풍성해지는 비주얼을 완성했다.",
        imageSrc: "/images/curation/cafe4_3.png",
        description2: "수플레 기법으로 구워낸 시트는 쫀득하면서도 촉촉한 질감을 지녔다. 포크로 푹 떠서 한입에 넣으면 부드러운 크림과 함께 압도적인 딸기 과즙이 터지며 상큼함을 한껏 끌어올린다.",
        mapImageSrc: "/images/curation/map4_3.png",
        listImageSrc: "/images/curation/cafe4_3.png",
      },
      {
        id: 16,
        name: "4. 아삐뽀레",
        shortDescription: "바삭한 타르트와 산뜻한 크림치즈 위로 쌓아 올린 생딸기",
        address: "서울특별시 용산구 위치 입력",
        description1: "고소한 아몬드 크림을 채워 단단하게 구워낸 바삭한 타르트지. 그 위로 눅진한 크림치즈와 신선한 생딸기를 산처럼 수북하게 쌓아 올려 테이블 위를 화사하게 밝혀주는 딸기 타르트다.",
        imageSrc: "/images/curation/cafe4_4.png",
        description2: "크림치즈 특유의 무거운 맛 대신, 과일의 새콤달콤함을 뒷받침해 주는 산뜻한 텍스처를 구현해 냈다. 바삭함과 부드러움, 그리고 딸기의 상큼함이 완벽한 삼박자를 이룬다.",
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
            className="w-full h-[180px] bg-[#F5F5F5] rounded-2xl mb-10 relative cursor-pointer overflow-hidden border border-gray-100 active:scale-[0.98] transition-transform"
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
               style={{ objectPosition: cafe.objectPosition || "center" }}
               sizes="(max-width: 768px) 100vw, 768px"
             />
          </div>
          <p className="text-[14px] text-[#616161] leading-[2.5] break-keep font-nanum mb-8">
            {cafe.description2}
          </p>
          
          {/* 지도 정적 이미지 영역 */}
          <div 
            className="w-full h-[180px] bg-[#F5F5F5] rounded-2xl relative cursor-pointer overflow-hidden border border-gray-100 active:scale-[0.98] transition-transform"
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