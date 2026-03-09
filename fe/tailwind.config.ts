import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./src/app/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/common/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/features/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        primary_btn_red: '#C3304F',  // 빨간 버튼
        primary_btn_gray: '#D9D9D9', // 회색 버튼
        bg_white: '#F8F8F3', // 배경
      },
      // layout.tsx의 폰트 변수와 연결
      fontFamily: {
        pretendard: ["var(--font-pretendard)", "sans-serif"],
        nanum_bold: ["var(--font-nanum-bold)", "sans-serif"],
        nanum_regular: ["var(--font-nanum-regular)", "sans-serif"],
      },
    },
  },
  plugins: [],
};

export default config;