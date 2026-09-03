import unittest
from datetime import date, datetime

from budget_app.validators import (
    normalize_required_text,
    normalize_category_name,
    normalize_optional_text,
    normalize_tags,
    parse_positive_int,
    validate_positive_int,
    parse_date,
    validate_date,
    parse_transaction_type,
    validate_transaction_type,
    parse_tags,
    parse_month,
    validate_month,
    validate_date_range,
    validate_export_filters,
)


class RequiredTextTest(unittest.TestCase):

    def test_normalize_required_text_strips_spaces(self):
        result = normalize_required_text(
            "  hello  ",
            "테스트"
        )

        self.assertEqual(result, "hello")

    def test_normalize_required_text_rejects_empty_string(self):
        with self.assertRaises(ValueError):
            normalize_required_text(
                "   ",
                "테스트"
            )

    def test_normalize_required_text_rejects_non_string(self):
        with self.assertRaises(ValueError):
            normalize_required_text(
                123,
                "테스트"
            )


class CategoryTest(unittest.TestCase):

    def test_category_is_lowercase(self):
        result = normalize_category_name("  FoOd  ")

        self.assertEqual(result, "food")


class PositiveIntTest(unittest.TestCase):

    def test_parse_positive_int_from_string(self):
        self.assertEqual(
            parse_positive_int(" 1000 ", "금액"),
            1000
        )

    def test_validate_positive_int_accepts_positive_integer(self):
        self.assertEqual(
            validate_positive_int(1000, "금액"),
            1000
        )

    def test_positive_int_rejects_zero(self):
        with self.assertRaises(ValueError):
            validate_positive_int(0, "금액")

    def test_positive_int_rejects_negative(self):
        with self.assertRaises(ValueError):
            validate_positive_int(-100, "금액")

    def test_positive_int_rejects_bool(self):
        with self.assertRaises(ValueError):
            validate_positive_int(True, "금액")


class DateTest(unittest.TestCase):

    def test_parse_date(self):
        result = parse_date(
            "2026-09-03",
            "날짜"
        )

        self.assertEqual(
            result,
            date(2026, 9, 3)
        )

    def test_invalid_date_rejected(self):
        with self.assertRaises(ValueError):
            parse_date(
                "2026-13-40",
                "날짜"
            )

    def test_datetime_rejected(self):
        with self.assertRaises(ValueError):
            validate_date(
                datetime(2026, 9, 3),
                "날짜"
            )


class TransactionTypeTest(unittest.TestCase):

    def test_parse_transaction_type_normalizes_case(self):
        self.assertEqual(
            parse_transaction_type(
                " INCOME ",
                "거래 유형"
            ),
            "income"
        )

    def test_invalid_transaction_type_rejected(self):
        with self.assertRaises(ValueError):
            validate_transaction_type(
                "deposit",
                "거래 유형"
            )


class TagTest(unittest.TestCase):

    def test_parse_tags_from_string(self):
        result = parse_tags(
            "food, lunch, food"
        )

        self.assertEqual(
            result,
            ["food", "lunch"]
        )

    def test_normalize_tags_removes_empty_and_duplicates(self):
        result = normalize_tags(
            [" food ", "", "food", " lunch "]
        )

        self.assertEqual(
            result,
            ["food", "lunch"]
        )


class MonthTest(unittest.TestCase):

    def test_parse_month(self):
        self.assertEqual(
            parse_month(
                " 2026-09 ",
                "월"
            ),
            "2026-09"
        )

    def test_invalid_month_rejected(self):
        with self.assertRaises(ValueError):
            validate_month(
                "2026-13",
                "월"
            )


class RangeTest(unittest.TestCase):

    def test_valid_date_range(self):
        validate_date_range(
            date(2026, 9, 1),
            date(2026, 9, 30)
        )

    def test_start_after_end_rejected(self):
        with self.assertRaises(ValueError):
            validate_date_range(
                date(2026, 9, 30),
                date(2026, 9, 1)
            )


class ExportFilterTest(unittest.TestCase):

    def test_month_is_valid_filter(self):
        validate_export_filters(
            "2026-09",
            None,
            None
        )

    def test_date_range_is_valid_filter(self):
        validate_export_filters(
            None,
            date(2026, 9, 1),
            date(2026, 9, 30)
        )

    def test_no_filter_rejected(self):
        with self.assertRaises(ValueError):
            validate_export_filters(
                None,
                None,
                None
            )

    def test_month_and_date_range_cannot_be_combined(self):
        with self.assertRaises(ValueError):
            validate_export_filters(
                "2026-09",
                date(2026, 9, 1),
                date(2026, 9, 30)
            )

    def test_only_start_date_rejected(self):
        with self.assertRaises(ValueError):
            validate_export_filters(
                None,
                date(2026, 9, 1),
                None
            )


if __name__ == "__main__":
    unittest.main()