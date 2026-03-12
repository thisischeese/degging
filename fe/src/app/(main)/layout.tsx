import BottomNav from "@/common/components/BottomNav";

export default function MainLayout({ children }: { children: React.ReactNode }) {
  return (
    <div className="flex flex-col h-full">
      <section className="flex-1 overflow-y-auto no-scrollbar">
        {children}
      </section>
      <BottomNav />
    </div>
  );
}