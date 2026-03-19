import './globals.css'; 
import localFont from 'next/font/local';
import Script from 'next/script';

import QueryProvider from '@/common/components/providers/QueryProvider';
import { MSWProvider } from '@/common/components/providers/MSWProvider'; // 1. 추가

export const metadata = {
  title: 'Degging',
  description: '디저트 큐레이션 서비스',
};

// Pretendard 설정
const pretendard = localFont({
  src: '../assets/fonts/PretendardVariable.ttf',
  variable: '--font-pretendard',
});

// NanumSquare 설정
const nanumB = localFont({
  src: '../assets/fonts/NanumSquareB.ttf',
  variable: '--font-nanum-bold',
});

const nanumR = localFont({
  src: '../assets/fonts/NanumSquareR.ttf',
  variable: '--font-nanum-regular',
});

export default function RootLayout({ children }: { children: React.ReactNode }) {
  const KAKAO_SDK_URL = `//dapi.kakao.com/v2/maps/sdk.js?appkey=${process.env.NEXT_PUBLIC_KAKAO_MAP_KEY}&autoload=false`;
  return (
    <html lang="ko" className={`${pretendard.variable} ${nanumB.variable} ${nanumR.variable}`}>
      <head>
        {/* 카카오 지도 스크립트 추가 */}
        <Script src={KAKAO_SDK_URL} strategy="beforeInteractive" />
        {/* Google Tag Manager */}
        <Script id="gtm-head" strategy="afterInteractive">
          {`(function(w,d,s,l,i){w[l]=w[l]||[];w[l].push({'gtm.start':
          new Date().getTime(),event:'gtm.js'});var f=d.getElementsByTagName(s)[0],
          j=d.createElement(s),dl=l!='dataLayer'?'&l='+l:'';j.async=true;j.src=
          'https://www.googletagmanager.com/gtm.js?id='+i+dl;f.parentNode.insertBefore(j,f);
          })(window,document,'script','dataLayer','GTM-5CPW52VB');`}
        </Script>
      </head>


      {/* 1. 배경색 지정 및 중앙 정렬 */}
      <body className="bg-gray-100 m-0 flex justify-center h-dvh font-pretendard overflow-hidden">
        {/* Google Tag Manager (noscript) */}
        <noscript>
          <iframe
            src="https://www.googletagmanager.com/ns.html?id=GTM-5CPW52VB"
            height="0"
            width="0"
            style={{ display: 'none', visibility: 'hidden' }}
          />
        </noscript>
        <MSWProvider>
          <QueryProvider>
            {/* 2. 앱 컨테이너 설정 */}
            <div className="w-full max-w-[375px] h-full bg-bg_white shadow-2xl relative flex flex-col overflow-hidden">
              {/* 3. 실제 콘텐츠 영역 */}
              <main className="flex-1 min-h-0 flex flex-col">
                {children}
              </main>
            </div>
          </QueryProvider>
        </MSWProvider>
      </body>
    </html>
  );
}