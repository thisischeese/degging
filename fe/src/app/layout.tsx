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
      <body className="font-pretendard"> {/* 기본 폰트 적용 */}
        <QueryProvider>
          {children}
        </QueryProvider>
      </body>
    </html>
  );
}