export default function MainLayout({ children }: { children: React.ReactNode }) {
  return (
    <section>
      {/* 하단 탭바(BottomNav)가 들어갈 자리 */}
      {children}
    </section>
  );
}