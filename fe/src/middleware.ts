import { NextResponse } from 'next/server'
import type { NextRequest } from 'next/server'

export function middleware(request: NextRequest) {
  const { pathname } = request.nextUrl
  const accessToken = request.cookies.get('access_token')?.value

  const isPublicPath = ['/login', '/signup', '/password', '/onboarding'].some(path => 
    pathname.startsWith(path)
  )

  // 1. 비회원이 루트(/)나 보호된 경로에 접근할 때
  if (!accessToken && !isPublicPath) {
    // degging.info/ 로 들어왔을 때 온보딩으로 리다이렉트
    return NextResponse.redirect(new URL('/onboarding', request.url))
  }

  // 2. 이미 로그인한 유저가 온보딩이나 로그인 페이지에 접근할 때 (선택 사항)
  if (accessToken && (pathname === '/onboarding' || pathname === '/login')) {
    return NextResponse.redirect(new URL('/', request.url))
  }

  return NextResponse.next()
}

// 미들웨어가 실행될 경로 설정
export const config = {
  matcher: [
    /*
     * 아래 경로를 제외한 모든 요청에서 미들웨어 실행:
     * - api (API routes)
     * - swagger-ui, v3/api-docs (Swagger docs)
     * - _next/static (static files)
     * - _next/image (image optimization files)
     * - images (public images)
     * - favicon.ico (favicon file)
     */
    '/((?!api|swagger-ui|v3/api-docs|_next/static|_next/image|images|favicon.ico).*)',
  ],
}
