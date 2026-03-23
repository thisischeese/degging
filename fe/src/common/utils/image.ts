export const getImageUrl = (path: string | null | undefined): string => {
  // 1. path가 없거나 빈 문자열일 경우 기본 이미지 반환
  if (!path) return "/images/common/logo.png";

  // 2. 이미 풀 경로(http...)인 경우 그대로 반환 (외부 링크 대응)
  if (path.startsWith("http")) return path;

  const domain = process.env.NEXT_PUBLIC_CLOUDFRONT_URL;

  // 3. 환경 변수가 없을 경우 대비 (콘솔에 경고를 띄우고 path만 반환)
  if (!domain) {
    console.warn("환경 변수 NEXT_PUBLIC_CLOUDFRONT_URL이 설정되지 않았습니다.");
    return path;
  }

  // 4. 도메인 끝과 경로 시작 부분의 슬래시(/) 중복 제거
  const cleanDomain = domain.endsWith("/") ? domain.slice(0, -1) : domain;
  const cleanPath = path.startsWith("/") ? path.slice(1) : path;

  // 최종 형태: https://domain.net/review/filename.jpg
  return `${cleanDomain}/${cleanPath}`;
};