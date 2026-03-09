from fastapi import FastAPI, HTTPException, Query
from crawler import run_crawl, DEFAULT_SEARCH_NAME

app = FastAPI(title="Cafe Crawl API")


@app.get("/crawl")
async def crawl(
    search_name: str = Query(
        default=DEFAULT_SEARCH_NAME,
        description="검색할 가게명 (예: 아우어베이커리 역삼점)",
    )
):
    """
    가게명을 받아 네이버 지도 탭별 크롤링을 실행한다.
    - 텍스트: output/{탭명}.txt
    - 사진: output/photos/photo_XX.jpg (최대 10장)
    - 메뉴사진: output/photos/menu/{메뉴명}.jpg
    """
    try:
        result = await run_crawl(search_name=search_name)
        return {
            "status": "ok",
            "search_name": search_name,
            "saved_texts": result["texts"],
            "saved_photos": result.get("photos", []),
            "saved_menu_photos": result.get("menu_photos", []),
            "saved_review_photos": result.get("review_photos", []),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
