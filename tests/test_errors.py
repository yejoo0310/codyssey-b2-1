import unittest

from budget_app.errors import (
    BudgetAppError,
    DataAccessError,
    DataFormatError,
    NotFoundError,
    DuplicateError,
    CategoryInUseError,
    ValidationError,
)


class BudgetAppErrorTest(unittest.TestCase):

    def test_message_and_hint(self):
        error = BudgetAppError(
            "문제가 발생했습니다.",
            hint="입력값을 확인하세요."
        )

        self.assertEqual(
            error.message,
            "문제가 발생했습니다."
        )

        self.assertEqual(
            error.hint,
            "입력값을 확인하세요."
        )

        self.assertEqual(
            str(error),
            "문제가 발생했습니다."
        )

    def test_custom_errors_inherit_budget_app_error(self):
        error_classes = [
            DataAccessError,
            DataFormatError,
            NotFoundError,
            DuplicateError,
            CategoryInUseError,
            ValidationError,
        ]

        for error_class in error_classes:
            with self.subTest(error_class=error_class):
                error = error_class("test")

                self.assertIsInstance(
                    error,
                    BudgetAppError
                )


if __name__ == "__main__":
    unittest.main()