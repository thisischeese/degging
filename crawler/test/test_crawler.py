import os
import shutil
import unittest
from pathlib import Path

from crawler.src.crawler import (
    load_settings,
    parse_business_hours_from_segments,
    parse_menu_text,
    parse_review_metrics,
)


class LoadSettingsTest(unittest.TestCase):
    def test_missing_required_env_keys_are_reported_by_name(self):
        tmpdir = Path.cwd() / "crawler" / "test" / "_tmp_env"
        tmpdir.mkdir(parents=True, exist_ok=True)
        try:
            env_path = tmpdir / ".env"
            env_path.write_text("S3_REGION=ap-northeast-2\n", encoding="utf-8")

            keys = ("S3_SECRET_KEY", "S3_ACCESS_KEY", "S3_BUCKET_NAME", "S3_REGION", "GMS_API_KEY")
            preserved = {key: os.environ.get(key) for key in keys}
            try:
                for key in keys:
                    os.environ.pop(key, None)
                with self.assertRaises(ValueError) as exc:
                    load_settings(env_path)
            finally:
                for key, value in preserved.items():
                    if value is None:
                        os.environ.pop(key, None)
                    else:
                        os.environ[key] = value

            message = str(exc.exception)
            self.assertIn("S3_SECRET_KEY", message)
            self.assertIn("S3_ACCESS_KEY", message)
            self.assertIn("S3_BUCKET_NAME", message)
            self.assertIn("GMS_API_KEY", message)
        finally:
            shutil.rmtree(tmpdir, ignore_errors=True)


class BusinessHoursParserTest(unittest.TestCase):
    def test_single_general_hours_fill_all_days(self):
        result = parse_business_hours_from_segments(["매일 10:00 - 22:00"])
        self.assertTrue(all(value == "10:00 - 22:00" for value in result.values()))

    def test_specific_day_hours_only_fill_specific_days(self):
        result = parse_business_hours_from_segments(["월 10:00 - 22:00", "토 휴무"])
        self.assertEqual(result["mon_hours"], "10:00 - 22:00")
        self.assertEqual(result["sat_hours"], "휴무")
        self.assertIsNone(result["tues_hours"])

    def test_specific_hours_override_general_hours(self):
        result = parse_business_hours_from_segments(["매일 10:00 - 22:00", "화 12:00 - 18:00"])
        self.assertEqual(result["mon_hours"], "10:00 - 22:00")
        self.assertEqual(result["tues_hours"], "12:00 - 18:00")
        self.assertEqual(result["sun_hours"], "10:00 - 22:00")


class MenuParserTest(unittest.TestCase):
    def test_menu_parser_handles_name_price_and_description(self):
        text = "\n".join(
            [
                "홈",
                "메뉴",
                "리뷰",
                "사진",
                "정보",
                "대표",
                "아메리카노",
                "4,500원",
                "시그니처 라떼",
                "부드러운 크림과 에스프레소",
                "6,000원",
            ]
        )
        menus = parse_menu_text(text)
        self.assertEqual(menus[0]["menu_name"], "아메리카노")
        self.assertEqual(menus[0]["price"], 4500)
        self.assertEqual(menus[1]["menu_name"], "시그니처 라떼")
        self.assertEqual(menus[1]["menu_description"], "부드러운 크림과 에스프레소")


class ReviewMetricsTest(unittest.TestCase):
    def test_review_metrics_fall_back_to_review_companion_ratios(self):
        text = "\n".join(
            [
                "홈",
                "메뉴",
                "리뷰",
                "사진",
                "정보",
                "방문자 리뷰 99",
                "리뷰 클렌징",
                "닉네임1",
                "리뷰 1사진 0",
                "팔로우",
                "점심에 방문예약 없이 이용대기 시간 바로 입장일상혼자",
                "별점 4",
                "혼자 오기 좋아요",
                "반응 남기기",
                "0",
                "닉네임2",
                "리뷰 1사진 0",
                "팔로우",
                "저녁에 방문예약 없이 이용대기 시간 바로 입장데이트친구",
                "별점 5",
                "분위기가 좋아요",
                "반응 남기기",
                "0",
            ]
        )
        metrics = parse_review_metrics(text)
        self.assertEqual(metrics["review_count"], 99)
        self.assertEqual(metrics["rating_sum"], 9)
        self.assertEqual(metrics["solo_ratio"], "0.500")
        self.assertEqual(metrics["friends_ratio"], "0.500")


if __name__ == "__main__":
    unittest.main()
