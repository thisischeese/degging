"use client";

import { useEffect, useState } from "react";
import { useRouter, usePathname } from "next/navigation";

interface AuthGuardProps {
  children: React.ReactNode;
}

export default function AuthGuard({ children }: AuthGuardProps) {
  const router = useRouter();
  const pathname = usePathname();
  const [isAuthorized, setIsAuthorized] = useState<boolean | null>(null);

  useEffect(() => {
    // 클라이언트 사이드에서만 실행
    const checkAuth = () => {
      const accessToken = sessionStorage.getItem("access_token");
      const publicPaths = ["/login", "/signup", "/password", "/onboarding"];
      const isPublicPath = publicPaths.some((path) => pathname.startsWith(path));

    if (!accessToken && !isPublicPath) {
      // 미들웨어가 이미 처리하지만, 클라이언트 사이드 보완을 위해 유지하거나 
      // 혹은 단순히 권한 없음 상태로만 둡니다.
      setIsAuthorized(false);
    } else {
      setIsAuthorized(true);
    }
    };

    checkAuth();
  }, [pathname, router]);

  // 인증이 확인된 경우에만 children 렌더링
  if (isAuthorized !== true) {
    return null; 
  }

  return <>{children}</>;
}
