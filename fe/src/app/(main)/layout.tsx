import BottomNav from "@/common/components/BottomNav";
import AuthGuard from "@/common/components/AuthGuard";

export default function MainLayout({ children }: { children: React.ReactNode }) {
  return (
    <AuthGuard>
      <div className="flex flex-col flex-1 min-h-0">
        <section className="flex-1 min-h-0 overflow-y-auto no-scrollbar">
          {children}
        </section>
        <BottomNav />
      </div>
    </AuthGuard>
  );
}