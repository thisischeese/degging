import './globals.css';

export const metadata = {
  title: 'Cafe App',
  description: '카페 추천 서비스',
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="ko">
      <body>{children}</body>
    </html>
  );
}