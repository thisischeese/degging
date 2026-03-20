import json
import shutil
import unittest
import uuid
from pathlib import Path

from crawler.scripts.preprocess_cafe_reviews import (
    build_cafe_reviews_payload,
    extract_cafe_reviews,
    strip_visit_meta_prefix,
)


class ReviewBoundaryTest(unittest.TestCase):
    def test_extract_with_more_marker(self):
        lines = [
            "머리말",
            "팔로우",
            "첫 번째 리뷰 문장",
            "두 번째 리뷰 문장",
            "더보기",
            "반응 남기기",
        ]
        reviews = extract_cafe_reviews("cafe-1", lines)
        self.assertEqual(len(reviews), 1)
        self.assertEqual(reviews[0]["user_review"], "첫 번째 리뷰 문장 두 번째 리뷰 문장")

    def test_extract_with_taste_marker(self):
        lines = [
            "팔로우",
            "분위기가 좋아요",
            "커피가 맛있어요+4",
            "반응 남기기",
        ]
        reviews = extract_cafe_reviews("cafe-2", lines)
        self.assertEqual(len(reviews), 1)
        self.assertEqual(reviews[0]["user_review"], "분위기가 좋아요")

    def test_extract_with_reaction_fallback(self):
        lines = [
            "팔로우",
            "늦은 시간에도 친절했어요",
            "반응 남기기",
            "방문일",
        ]
        reviews = extract_cafe_reviews("cafe-3", lines)
        self.assertEqual(len(reviews), 1)
        self.assertEqual(reviews[0]["user_review"], "늦은 시간에도 친절했어요")

    def test_extract_without_follow_marker(self):
        lines = ["리뷰 없음", "더보기"]
        reviews = extract_cafe_reviews("cafe-4", lines)
        self.assertEqual(reviews, [])

    def test_user_id_is_stable_uuid5(self):
        lines = ["팔로우", "고소한 라떼가 좋아요", "더보기"]
        first = extract_cafe_reviews("cafe-5", lines)
        second = extract_cafe_reviews("cafe-5", lines)
        self.assertEqual(first[0]["user_id"], second[0]["user_id"])
        self.assertEqual(uuid.UUID(first[0]["user_id"]).version, 5)


class VisitMetaPrefixCleanupTest(unittest.TestCase):
    def test_strip_visit_meta_prefix_evening_case(self):
        text = "저녁에 방문예약 없이 이용대기 시간 바로 입장일상연인・배우자 맛있어요"
        self.assertEqual(strip_visit_meta_prefix(text), "맛있어요")

    def test_strip_visit_meta_prefix_lunch_delivery_case(self):
        text = "점심에 방문포장·배달 이용대기 시간 바로 입장 분위기가 좋아요"
        self.assertEqual(strip_visit_meta_prefix(text), "분위기가 좋아요")

    def test_strip_visit_meta_prefix_morning_delivery_case(self):
        text = "아침에 방문포장·배달 이용대기 시간 바로 입장 커피가 좋아요"
        self.assertEqual(strip_visit_meta_prefix(text), "커피가 좋아요")

    def test_strip_visit_meta_prefix_video_next_case(self):
        text = "동영상 다음 점심에 방문예약 없이 이용대기 시간 바로 입장 파스타가 맛있어요"
        self.assertEqual(strip_visit_meta_prefix(text), "파스타가 맛있어요")

    def test_non_meta_sentence_is_preserved(self):
        text = "점심에 방문했는데 파스타가 맛있어요"
        self.assertEqual(strip_visit_meta_prefix(text), text)

    def test_boundary_extraction_regression_kept(self):
        lines = [
            "팔로우",
            "점심에 방문포장·배달 이용대기 시간 바로 입장일상혼자",
            "테이크아웃 전문이라 빨라요",
            "더보기",
            "반응 남기기",
        ]
        reviews = extract_cafe_reviews("cafe-meta-1", lines)
        self.assertEqual(len(reviews), 1)
        self.assertEqual(reviews[0]["user_review"], "테이크아웃 전문이라 빨라요")


class PayloadSchemaTest(unittest.TestCase):
    def test_payload_schema_and_empty_review_cafe(self):
        tmp_root_base = Path.cwd() / "crawler" / "test" / "_tmp_review_preprocess"
        tmp_root_base.mkdir(parents=True, exist_ok=True)
        tmp = tmp_root_base / f"case_{uuid.uuid4().hex}"
        tmp.mkdir(parents=True, exist_ok=True)
        try:
            enriched_path = tmp / "cafe_enriched.json"
            output_root = tmp / "output"

            cafe_a = "11111111-1111-1111-1111-111111111111"
            cafe_b = "22222222-2222-2222-2222-222222222222"

            enriched_rows = [{"cafe_id": cafe_a}, {"cafe_id": cafe_b}]
            enriched_path.write_text(json.dumps(enriched_rows, ensure_ascii=False), encoding="utf-8")

            review_path_a = output_root / cafe_a / "texts" / "review.txt"
            review_path_a.parent.mkdir(parents=True, exist_ok=True)
            review_path_a.write_text(
                "\n".join(
                    [
                        "팔로우",
                        "좌석이 넓고 조용해요",
                        "더보기",
                    ]
                ),
                encoding="utf-8",
            )

            payload = build_cafe_reviews_payload(enriched_path, output_root)
            self.assertEqual(len(payload), 2)
            self.assertEqual(payload[0]["cafe_id"], cafe_a)
            self.assertEqual(payload[1]["cafe_id"], cafe_b)
            self.assertEqual(payload[1]["cafe_reviews"], [])

            first_review = payload[0]["cafe_reviews"][0]
            self.assertEqual(set(first_review.keys()), {"user_id", "user_review"})
            self.assertEqual(first_review["user_review"], "좌석이 넓고 조용해요")
            uuid.UUID(first_review["user_id"])
        finally:
            shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    unittest.main()
