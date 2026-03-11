import './globals.css'; 
import localFont from 'next/font/local';
import QueryProvider from '@/common/components/providers/QueryProvider';

export const metadata = {
  title: 'Degging',
  description: '디저트 큐레이션 서비스',
};

// 1. Pretendard 설정
const pretendard = localFont({
  src: '../assets/fonts/PretendardVariable.ttf',
  variable: '--font-pretendard',
});

// 2. NanumSquare 설정
const nanumB = localFont({
  src: '../assets/fonts/NanumSquareB.ttf',
  variable: '--font-nanum-bold',
});

const nanumR = localFont({
  src: '../assets/fonts/NanumSquareR.ttf',
  variable: '--font-nanum-regular',
});

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="ko" className={`${pretendard.variable} ${nanumB.variable} ${nanumR.variable}`}>
      {/* 1. 배경색 지정 및 중앙 정렬 */}
      <body 
      className="bg-gray-100 m-0 flex justify-center min-h-screen font-pretendard"> 
        <QueryProvider>
          {/* 2. 앱 컨테이너 설정 */}
          <div className="w-full max-w-[375px] min-h-screen bg-bg_white shadow-2xl relative flex flex-col overflow-x-hidden">
            {/* 3. 실제 콘텐츠 영역 */}
            <main className="flex-1 w-full">
              {children}
            </main>
          </div>
        </QueryProvider>
      </body>
    </html>
  );
}