import unittest
from datetime import date

from budget_app.models import (
    Transaction,
    Budget,
    Category,
    MonthlySummary,
    ImportResult,
)


class TransactionTest(unittest.TestCase):

    def test_create_transaction_normalizes_values(self):
        transaction = Transaction(
            id=" TX-000001 ",
            type="expense",
            date=date(2026, 9, 3),
            amount=15000,
            category=" FOOD ",
            memo=" lunch ",
            tags=[" meal ", "meal", ""]
        )

        self.assertEqual(
            transaction.id,
            "TX-000001"
        )

        self.assertEqual(
            transaction.category,
            "food"
        )

        self.assertEqual(
            transaction.memo,
            "lunch"
        )

        self.assertEqual(
            transaction.tags,
            ["meal"]
        )

    def test_invalid_amount_rejected(self):
        with self.assertRaises(ValueError):
            Transaction(
                id="TX-000001",
                type="expense",
                date=date(2026, 9, 3),
                amount=0,
                category="food",
            )

    def test_invalid_type_rejected(self):
        with self.assertRaises(ValueError):
            Transaction(
                id="TX-000001",
                type="wrong",
                date=date(2026, 9, 3),
                amount=1000,
                category="food",
            )

    def test_to_dict(self):
        transaction = Transaction(
            id="TX-000001",
            type="expense",
            date=date(2026, 9, 3),
            amount=15000,
            category="food",
            memo="점심",
            tags=["meal"]
        )

        result = transaction.to_dict()

        self.assertEqual(
            result,
            {
                "id": "TX-000001",
                "type": "expense",
                "date": "2026-09-03",
                "amount": 15000,
                "category": "food",
                "memo": "점심",
                "tags": ["meal"],
            }
        )

    def test_from_dict(self):
        transaction = Transaction.from_dict(
            {
                "id": "TX-000001",
                "type": " EXPENSE ",
                "date": "2026-09-03",
                "amount": "15000",
                "category": " FOOD ",
                "memo": " 점심 ",
                "tags": ["meal"]
            }
        )

        self.assertEqual(
            transaction.date,
            date(2026, 9, 3)
        )

        self.assertEqual(
            transaction.amount,
            15000
        )

        self.assertEqual(
            transaction.category,
            "food"
        )

    def test_from_dict_missing_required_field(self):
        with self.assertRaises(ValueError):
            Transaction.from_dict(
                {
                    "type": "expense",
                    "date": "2026-09-03",
                    "amount": 1000,
                    "category": "food",
                }
            )


class BudgetTest(unittest.TestCase):

    def test_create_budget(self):
        budget = Budget(
            month="2026-09",
            amount=500000
        )

        self.assertEqual(
            budget.month,
            "2026-09"
        )

        self.assertEqual(
            budget.amount,
            500000
        )

    def test_invalid_month_rejected(self):
        with self.assertRaises(ValueError):
            Budget(
                month="2026-13",
                amount=500000
            )

    def test_budget_from_dict(self):
        budget = Budget.from_dict(
            {
                "month": "2026-09",
                "amount": "500000"
            }
        )

        self.assertEqual(
            budget.amount,
            500000
        )


class CategoryTest(unittest.TestCase):

    def test_category_normalized(self):
        category = Category(
            name=" FOOD "
        )

        self.assertEqual(
            category.name,
            "food"
        )

    def test_category_is_frozen(self):
        category = Category(
            name="food"
        )

        with self.assertRaises(Exception):
            category.name = "transport"


class SimpleModelTest(unittest.TestCase):

    def test_import_result(self):
        result = ImportResult(
            imported=5,
            skipped=2
        )

        self.assertEqual(result.imported, 5)
        self.assertEqual(result.skipped, 2)


if __name__ == "__main__":
    unittest.main()