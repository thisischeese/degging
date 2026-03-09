## 🍰 Degging
사용자의 취향을 분석하여 최적의 카페를 매칭해주는 AI 개인화 추천 서비스

## 🚀 프로젝트 소개
단순한 위치 기반 검색을 넘어, 사용자의 고유한 취향을 반영한 초개인화된 카페 큐레이션을 제공합니다. 데이터가 축적될수록 유저의 의도를 정확히 파악하여 정보 탐색 비용을 획기적으로 줄여주는 스마트한 카페 및 디저트 가이드를 지향합니다.

## 🛠 Tech Stack
**✅ Front-end**<br>
Framework: Next.js 14 (App Router)

Language: TypeScript

State Management: Zustand

Styling: Tailwind CSS

Data Fetching: Axios / TanStack Query

Deployment: Vercel

**✅ Back-end**<br>
Core: Java 17 / Spring Boot

Database: PostgreSQL (Main), Redis (Cache), MongoDB

**✅ AI**<br>
Search: FastAPI + Hybrid Search (Vector & Keyword)

AI / Data
Models: CLIP (Image Analysis), KoSimCSE (Embedding)

LLM: GPT-4 / Claude (Curation Comment Generation)

## 📂 Project Structure
```
├── ai/         # AI Model Serving (FastAPI)
├── be/         # Main Back-end (Spring Boot)
├── fe/         # Front-end (Next.js)
└── docker-compose.yml
```

## ✨ Key Features
개인화 온보딩: 이미지와 키워드 선택을 통한 초기 취향 벡터 산출

실시간 트렌드 분석: 외부 데이터와 유저 로그 기반 급상승 디저트 랭킹

하이브리드 서치: 사용자 위치와 취향 벡터를 결합한 고도화된 카페 추천

AI 추천 코멘트: "당신의 취향인 우드톤과 푸딩이 있는 곳이에요"와 같은 맞춤형 사유 제공


## 👥 Team


| [공지윤](https://github.com/kongsh621) | [김다희](https://github.com/K-DaHee) | [윤지선]() |
| --- | --- | --- |
| <img src="./assets/공지윤.png"> | <img src="./assets/김다희.png"> | <img src="./assets/윤지선.png"> |
| **Backend** | **Backend** | **Frontend** |

| [이수빈](https://github.com/subbb-in) | [최다은]() | [최지희]() |
| --- | --- | --- |
| <img src="./assets/이수빈.png"> | <img src="./assets/최다은.png" > | <img src="./assets/최지희.png"> |
| **Infra** | **AI** | **Frontend** |