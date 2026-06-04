import unittest

import naver_map_menu_hours as standalone


class NaverMapMenuHoursTest(unittest.TestCase):
    def test_build_output_payload_counts_non_success_as_failed(self) -> None:
        payload = standalone.build_output_payload(
            [
                {"status": "success"},
                {"status": "not_found"},
                {"status": "error"},
            ]
        )

        self.assertEqual(payload["requested"], 3)
        self.assertEqual(payload["succeeded"], 1)
        self.assertEqual(payload["failed"], 2)

    def test_build_structured_business_hours_maps_rows(self) -> None:
        business_hours = standalone.build_structured_business_hours(
            [
                {"day": "월", "time": "08:00 - 20:00"},
                {"day": "화요일", "time": "휴무"},
                {"day": "토", "time": "10:00 - 18:00"},
                {"day": "", "time": "ignore"},
            ]
        )

        self.assertEqual(
            business_hours,
            {
                "mon_hours": "08:00 - 20:00",
                "tues_hours": "휴무",
                "wed_hours": None,
                "thur_hours": None,
                "fri_hours": None,
                "sat_hours": "10:00 - 18:00",
                "sun_hours": None,
            },
        )

    def test_build_menus_with_candidates_matches_fifo_and_falls_back(self) -> None:
        menu_cards = [
            standalone.MenuCardPayload(
                menu_name="Americano",
                image_url="https://ldb-phinf.pstatic.net/20250325_1/americano-0.jpg",
            ),
            standalone.MenuCardPayload(
                menu_name="Latte",
                price=5000,
                menu_description="milk",
            ),
            standalone.MenuCardPayload(
                menu_name="Americano",
                price=4700,
            ),
        ]

        original_parse = standalone.parse_menu_text
        standalone.parse_menu_text = lambda _text: [
            {"menu_name": "Americano", "price": 4500, "menu_description": None},
            {"menu_name": "Latte", "price": None, "menu_description": None},
            {"menu_name": "Americano", "price": None, "menu_description": None},
            {"menu_name": "Mocha", "price": None, "menu_description": None},
        ]
        try:
            menus = standalone.build_menus_with_candidates("ignored", menu_cards)
        finally:
            standalone.parse_menu_text = original_parse

        self.assertEqual(
            menus,
            [
                {"menu_name": "Americano", "price": 4500, "menu_description": None},
                {"menu_name": "Latte", "price": 5000, "menu_description": "milk"},
                {"menu_name": "Americano", "price": 4700, "menu_description": None},
                {"menu_name": "Mocha", "price": None, "menu_description": None},
            ],
        )

    def test_build_menus_with_candidates_uses_cards_when_text_parse_is_empty(self) -> None:
        menu_cards = [
            standalone.MenuCardPayload(
                menu_name="Signature Latte",
                price=6500,
                menu_description="cream top",
            )
        ]

        original_parse = standalone.parse_menu_text
        standalone.parse_menu_text = lambda _text: []
        try:
            menus = standalone.build_menus_with_candidates("ignored", menu_cards)
        finally:
            standalone.parse_menu_text = original_parse

        self.assertEqual(
            menus,
            [
                {
                    "menu_name": "Signature Latte",
                    "price": 6500,
                    "menu_description": "cream top",
                }
            ],
        )

    def test_parse_business_hours_handles_weekday_and_specific_overrides(self) -> None:
        parsed = standalone.parse_business_hours(
            "영업시간\n평일 08:00 - 20:00\n주말 10:00 - 18:00\n화 09:00 - 21:00",
            "",
        )

        self.assertEqual(
            parsed,
            {
                "mon_hours": "08:00 - 20:00",
                "tues_hours": "09:00 - 21:00",
                "wed_hours": "08:00 - 20:00",
                "thur_hours": "08:00 - 20:00",
                "fri_hours": "08:00 - 20:00",
                "sat_hours": "10:00 - 18:00",
                "sun_hours": "10:00 - 18:00",
            },
        )


if __name__ == "__main__":
    unittest.main()
