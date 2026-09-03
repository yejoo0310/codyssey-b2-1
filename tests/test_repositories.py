import tempfile
import unittest

from datetime import date
from pathlib import Path

from budget_app.errors import (
    DataFormatError,
    DuplicateError,
    NotFoundError,
)
from budget_app.models import (
    Budget,
    Category,
    Transaction,
)
from budget_app.repositories import (
    BudgetRepository,
    CategoryRepository,
    TransactionRepository,
)


class TransactionRepositoryTest(unittest.TestCase):

    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()

        self.file_path = (
            Path(self.temp_dir.name)
            / "transactions.jsonl"
        )

        self.repository = TransactionRepository(
            self.file_path
        )

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def make_transaction(
        self,
        transaction_id: str = "TX-000001",
        *,
        transaction_type: str = "expense",
        transaction_date: date = date(2026, 9, 3),
        amount: int = 10000,
        category: str = "food",
        memo: str = "점심",
        tags: list[str] | None = None,
    ) -> Transaction:
        return Transaction(
            id=transaction_id,
            type=transaction_type,
            date=transaction_date,
            amount=amount,
            category=category,
            memo=memo,
            tags=(
                tags
                if tags is not None
                else ["meal"]
            ),
        )

    # --------------------------------------------------
    # 파일 생성
    # --------------------------------------------------

    def test_repository_creates_file(self) -> None:
        self.assertTrue(
            self.file_path.exists()
        )

    # --------------------------------------------------
    # add
    # --------------------------------------------------

    def test_add_saves_transaction(self) -> None:
        transaction = self.make_transaction()

        self.repository.add(transaction)

        saved_transactions = list(
            self.repository.iter_all()
        )

        self.assertEqual(
            len(saved_transactions),
            1
        )

        self.assertEqual(
            saved_transactions[0],
            transaction
        )

    def test_add_writes_jsonl_file(self) -> None:
        transaction = self.make_transaction()

        self.repository.add(transaction)

        content = self.file_path.read_text(
            encoding="utf-8"
        )

        self.assertIn(
            '"id": "TX-000001"',
            content
        )

        self.assertIn(
            '"amount": 10000',
            content
        )

    def test_add_duplicate_id_raises_duplicate_error(
        self
    ) -> None:
        transaction = self.make_transaction()

        self.repository.add(transaction)

        with self.assertRaises(DuplicateError):
            self.repository.add(transaction)

    # --------------------------------------------------
    # exists
    # --------------------------------------------------

    def test_exists_returns_true_when_transaction_exists(
        self
    ) -> None:
        transaction = self.make_transaction()

        self.repository.add(transaction)

        self.assertTrue(
            self.repository.exists(
                "TX-000001"
            )
        )

    def test_exists_returns_false_when_transaction_does_not_exist(
        self
    ) -> None:
        self.assertFalse(
            self.repository.exists(
                "TX-999999"
            )
        )

    # --------------------------------------------------
    # get_by_id
    # --------------------------------------------------

    def test_get_by_id_returns_transaction(
        self
    ) -> None:
        transaction = self.make_transaction()

        self.repository.add(transaction)

        saved = self.repository.get_by_id(
            "TX-000001"
        )

        self.assertEqual(
            saved,
            transaction
        )

    def test_get_by_id_raises_not_found_error(
        self
    ) -> None:
        with self.assertRaises(NotFoundError):
            self.repository.get_by_id(
                "TX-999999"
            )

    # --------------------------------------------------
    # iter_all
    # --------------------------------------------------

    def test_iter_all_returns_all_transactions_in_file_order(
        self
    ) -> None:
        first = self.make_transaction(
            "TX-000001",
            amount=10000,
        )

        second = self.make_transaction(
            "TX-000002",
            amount=20000,
        )

        third = self.make_transaction(
            "TX-000003",
            amount=30000,
        )

        self.repository.add(first)
        self.repository.add(second)
        self.repository.add(third)

        transactions = list(
            self.repository.iter_all()
        )

        self.assertEqual(
            transactions,
            [
                third,
                second,
                first,
            ]
        )

    def test_iter_all_empty_file_returns_empty_list(
        self
    ) -> None:
        transactions = list(
            self.repository.iter_all()
        )

        self.assertEqual(
            transactions,
            []
        )

    # --------------------------------------------------
    # generate_id
    # --------------------------------------------------

    def test_generate_id_returns_first_id_when_empty(
        self
    ) -> None:
        self.assertEqual(
            self.repository.generate_id(),
            "TX-000001"
        )

    def test_generate_id_returns_next_id(
        self
    ) -> None:
        self.repository.add(
            self.make_transaction(
                "TX-000001"
            )
        )

        self.repository.add(
            self.make_transaction(
                "TX-000002"
            )
        )

        self.assertEqual(
            self.repository.generate_id(),
            "TX-000003"
        )

    def test_generate_id_uses_max_existing_number(
        self
    ) -> None:
        self.repository.add(
            self.make_transaction(
                "TX-000003"
            )
        )

        self.repository.add(
            self.make_transaction(
                "TX-000010"
            )
        )

        self.repository.add(
            self.make_transaction(
                "TX-000005"
            )
        )

        self.assertEqual(
            self.repository.generate_id(),
            "TX-000011"
        )

    def test_generate_id_ignores_invalid_id_format(
        self
    ) -> None:
        invalid_id_transaction = self.make_transaction(
            "CUSTOM-ID"
        )

        valid_id_transaction = self.make_transaction(
            "TX-000003"
        )

        self.repository.add(
            invalid_id_transaction
        )

        self.repository.add(
            valid_id_transaction
        )

        self.assertEqual(
            self.repository.generate_id(),
            "TX-000004"
        )

    # --------------------------------------------------
    # update
    # --------------------------------------------------

    def test_update_replaces_matching_transaction(
        self
    ) -> None:
        original = self.make_transaction(
            "TX-000001",
            amount=10000,
        )

        self.repository.add(original)

        updated = self.make_transaction(
            "TX-000001",
            amount=50000,
            memo="수정된 메모",
        )

        self.repository.update(updated)

        saved = self.repository.get_by_id(
            "TX-000001"
        )

        self.assertEqual(
            saved.amount,
            50000
        )

        self.assertEqual(
            saved.memo,
            "수정된 메모"
        )

    def test_update_replaces_only_matching_transaction(
        self
    ) -> None:
        first = self.make_transaction(
            "TX-000001",
            amount=10000,
        )

        second = self.make_transaction(
            "TX-000002",
            amount=20000,
        )

        self.repository.add(first)
        self.repository.add(second)

        updated = self.make_transaction(
            "TX-000001",
            amount=50000,
        )

        self.repository.update(updated)

        transactions = list(
            self.repository.iter_all()
        )

        self.assertEqual(
            len(transactions),
            2
        )

        self.assertEqual(
            transactions[1].id,
            "TX-000001"
        )

        self.assertEqual(
            transactions[1].amount,
            50000
        )

        self.assertEqual(
            transactions[0].id,
            "TX-000002"
        )

        self.assertEqual(
            transactions[0].amount,
            20000
        )

    def test_update_keeps_transaction_order(
        self
    ) -> None:
        first = self.make_transaction(
            "TX-000001"
        )

        second = self.make_transaction(
            "TX-000002"
        )

        third = self.make_transaction(
            "TX-000003"
        )

        self.repository.add(first)
        self.repository.add(second)
        self.repository.add(third)

        updated_second = self.make_transaction(
            "TX-000002",
            amount=99999,
        )

        self.repository.update(
            updated_second
        )

        transactions = list(
            self.repository.iter_all()
        )

        self.assertEqual(
            [
                transaction.id
                for transaction in transactions
            ],
            [
                "TX-000003",
                "TX-000002",
                "TX-000001",
            ]
        )

    def test_update_missing_transaction_raises_not_found_error(
        self
    ) -> None:
        transaction = self.make_transaction(
            "TX-999999"
        )

        with self.assertRaises(NotFoundError):
            self.repository.update(
                transaction
            )

    # --------------------------------------------------
    # delete
    # --------------------------------------------------

    def test_delete_removes_transaction(
        self
    ) -> None:
        transaction = self.make_transaction()

        self.repository.add(transaction)

        self.repository.delete(
            "TX-000001"
        )

        self.assertFalse(
            self.repository.exists(
                "TX-000001"
            )
        )

    def test_delete_removes_only_matching_transaction(
        self
    ) -> None:
        first = self.make_transaction(
            "TX-000001"
        )

        second = self.make_transaction(
            "TX-000002"
        )

        third = self.make_transaction(
            "TX-000003"
        )

        self.repository.add(first)
        self.repository.add(second)
        self.repository.add(third)

        self.repository.delete(
            "TX-000002"
        )

        transactions = list(
            self.repository.iter_all()
        )

        self.assertEqual(
            [
                transaction.id
                for transaction in transactions
            ],
            [
                "TX-000003",
                "TX-000001",
            ]
        )

    def test_delete_missing_transaction_raises_not_found_error(
        self
    ) -> None:
        with self.assertRaises(NotFoundError):
            self.repository.delete(
                "TX-999999"
            )

    # --------------------------------------------------
    # 잘못된 JSONL
    # --------------------------------------------------

    def test_iter_all_invalid_json_raises_data_format_error(
        self
    ) -> None:
        self.file_path.write_text(
            "this is not json\n",
            encoding="utf-8"
        )

        with self.assertRaises(DataFormatError):
            list(
                self.repository.iter_all()
            )

    def test_iter_all_non_object_json_raises_data_format_error(
        self
    ) -> None:
        self.file_path.write_text(
            '["TX-000001", "expense"]\n',
            encoding="utf-8"
        )

        with self.assertRaises(DataFormatError):
            list(
                self.repository.iter_all()
            )

    def test_iter_all_invalid_transaction_data_raises_data_format_error(
        self
    ) -> None:
        self.file_path.write_text(
            '{"id": "TX-000001"}\n',
            encoding="utf-8"
        )

        with self.assertRaises(DataFormatError):
            list(
                self.repository.iter_all()
            )

    def test_iter_all_ignores_blank_lines(
        self
    ) -> None:
        transaction = self.make_transaction()

        self.repository.add(transaction)

        original = self.file_path.read_text(
            encoding="utf-8"
        )

        self.file_path.write_text(
            "\n"
            + original
            + "\n\n",
            encoding="utf-8"
        )

        transactions = list(
            self.repository.iter_all()
        )

        self.assertEqual(
            len(transactions),
            1
        )


class CategoryRepositoryTest(unittest.TestCase):

    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()

        self.file_path = (
            Path(self.temp_dir.name)
            / "categories.jsonl"
        )

        self.repository = CategoryRepository(
            self.file_path
        )

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    # --------------------------------------------------
    # 파일 생성
    # --------------------------------------------------

    def test_repository_creates_file(self) -> None:
        self.assertTrue(
            self.file_path.exists()
        )

    # --------------------------------------------------
    # add
    # --------------------------------------------------

    def test_add_saves_category(self) -> None:
        category = Category(
            name="food"
        )

        self.repository.add(category)

        categories = list(
            self.repository.iter_all()
        )

        self.assertEqual(
            categories,
            [category]
        )

    def test_add_normalized_category(
        self
    ) -> None:
        category = Category(
            name=" FoOd "
        )

        self.repository.add(category)

        saved = self.repository.get_by_name(
            "food"
        )

        self.assertEqual(
            saved.name,
            "food"
        )

    def test_add_duplicate_category_raises_duplicate_error(
        self
    ) -> None:
        self.repository.add(
            Category("food")
        )

        with self.assertRaises(DuplicateError):
            self.repository.add(
                Category("food")
            )

    def test_duplicate_category_is_case_insensitive(
        self
    ) -> None:
        self.repository.add(
            Category("food")
        )

        with self.assertRaises(DuplicateError):
            self.repository.add(
                Category("FOOD")
            )

    # --------------------------------------------------
    # exists
    # --------------------------------------------------

    def test_exists_returns_true_when_category_exists(
        self
    ) -> None:
        self.repository.add(
            Category("food")
        )

        self.assertTrue(
            self.repository.exists(
                "food"
            )
        )

    def test_exists_is_case_insensitive(
        self
    ) -> None:
        self.repository.add(
            Category("food")
        )

        self.assertTrue(
            self.repository.exists(
                "FOOD"
            )
        )

        self.assertTrue(
            self.repository.exists(
                " Food "
            )
        )

    def test_exists_returns_false_when_category_does_not_exist(
        self
    ) -> None:
        self.assertFalse(
            self.repository.exists(
                "unknown"
            )
        )

    # --------------------------------------------------
    # get_by_name
    # --------------------------------------------------

    def test_get_by_name_returns_category(
        self
    ) -> None:
        category = Category(
            "food"
        )

        self.repository.add(category)

        saved = self.repository.get_by_name(
            "food"
        )

        self.assertEqual(
            saved,
            category
        )

    def test_get_by_name_is_case_insensitive(
        self
    ) -> None:
        self.repository.add(
            Category("food")
        )

        saved = self.repository.get_by_name(
            " FOOD "
        )

        self.assertEqual(
            saved.name,
            "food"
        )

    def test_get_by_name_missing_category_raises_not_found_error(
        self
    ) -> None:
        with self.assertRaises(NotFoundError):
            self.repository.get_by_name(
                "unknown"
            )

    # --------------------------------------------------
    # iter_all
    # --------------------------------------------------

    def test_iter_all_returns_categories_in_file_order(
        self
    ) -> None:
        food = Category("food")
        transport = Category("transport")
        rent = Category("rent")

        self.repository.add(food)
        self.repository.add(transport)
        self.repository.add(rent)

        categories = list(
            self.repository.iter_all()
        )

        self.assertEqual(
            categories,
            [
                food,
                transport,
                rent,
            ]
        )

    # --------------------------------------------------
    # remove
    # --------------------------------------------------

    def test_remove_category(
        self
    ) -> None:
        self.repository.add(
            Category("food")
        )

        self.repository.remove(
            "food"
        )

        self.assertFalse(
            self.repository.exists(
                "food"
            )
        )

    def test_remove_is_case_insensitive(
        self
    ) -> None:
        self.repository.add(
            Category("food")
        )

        self.repository.remove(
            " FOOD "
        )

        self.assertFalse(
            self.repository.exists(
                "food"
            )
        )

    def test_remove_only_matching_category(
        self
    ) -> None:
        self.repository.add(
            Category("food")
        )

        self.repository.add(
            Category("transport")
        )

        self.repository.add(
            Category("rent")
        )

        self.repository.remove(
            "transport"
        )

        categories = list(
            self.repository.iter_all()
        )

        self.assertEqual(
            [
                category.name
                for category in categories
            ],
            [
                "food",
                "rent",
            ]
        )

    def test_remove_missing_category_raises_not_found_error(
        self
    ) -> None:
        with self.assertRaises(NotFoundError):
            self.repository.remove(
                "unknown"
            )

    # --------------------------------------------------
    # 잘못된 JSONL
    # --------------------------------------------------

    def test_iter_all_invalid_json_raises_data_format_error(
        self
    ) -> None:
        self.file_path.write_text(
            "not json\n",
            encoding="utf-8"
        )

        with self.assertRaises(DataFormatError):
            list(
                self.repository.iter_all()
            )

    def test_iter_all_invalid_category_data_raises_data_format_error(
        self
    ) -> None:
        self.file_path.write_text(
            '{"wrong": "food"}\n',
            encoding="utf-8"
        )

        with self.assertRaises(DataFormatError):
            list(
                self.repository.iter_all()
            )


class BudgetRepositoryTest(unittest.TestCase):

    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()

        self.file_path = (
            Path(self.temp_dir.name)
            / "budgets.jsonl"
        )

        self.repository = BudgetRepository(
            self.file_path
        )

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    # --------------------------------------------------
    # 파일 생성
    # --------------------------------------------------

    def test_repository_creates_file(
        self
    ) -> None:
        self.assertTrue(
            self.file_path.exists()
        )

    # --------------------------------------------------
    # set
    # --------------------------------------------------

    def test_set_adds_new_budget(
        self
    ) -> None:
        budget = Budget(
            month="2026-09",
            amount=500000,
        )

        self.repository.set(budget)

        budgets = list(
            self.repository.iter_all()
        )

        self.assertEqual(
            budgets,
            [budget]
        )

    def test_set_replaces_existing_budget(
        self
    ) -> None:
        original = Budget(
            month="2026-09",
            amount=500000,
        )

        updated = Budget(
            month="2026-09",
            amount=700000,
        )

        self.repository.set(original)
        self.repository.set(updated)

        budgets = list(
            self.repository.iter_all()
        )

        self.assertEqual(
            len(budgets),
            1
        )

        self.assertEqual(
            budgets[0].amount,
            700000
        )

    def test_set_updates_only_matching_month(
        self
    ) -> None:
        september = Budget(
            month="2026-09",
            amount=500000,
        )

        october = Budget(
            month="2026-10",
            amount=600000,
        )

        self.repository.set(september)
        self.repository.set(october)

        updated_september = Budget(
            month="2026-09",
            amount=900000,
        )

        self.repository.set(
            updated_september
        )

        budgets = list(
            self.repository.iter_all()
        )

        self.assertEqual(
            len(budgets),
            2
        )

        self.assertEqual(
            budgets[0].month,
            "2026-09"
        )

        self.assertEqual(
            budgets[0].amount,
            900000
        )

        self.assertEqual(
            budgets[1].month,
            "2026-10"
        )

        self.assertEqual(
            budgets[1].amount,
            600000
        )

    # --------------------------------------------------
    # exists
    # --------------------------------------------------

    def test_exists_returns_true_when_budget_exists(
        self
    ) -> None:
        self.repository.set(
            Budget(
                month="2026-09",
                amount=500000,
            )
        )

        self.assertTrue(
            self.repository.exists(
                "2026-09"
            )
        )

    def test_exists_returns_false_when_budget_does_not_exist(
        self
    ) -> None:
        self.assertFalse(
            self.repository.exists(
                "2026-09"
            )
        )

    # --------------------------------------------------
    # get_by_month
    # --------------------------------------------------

    def test_get_by_month_returns_budget(
        self
    ) -> None:
        budget = Budget(
            month="2026-09",
            amount=500000,
        )

        self.repository.set(budget)

        saved = self.repository.get_by_month(
            "2026-09"
        )

        self.assertEqual(
            saved,
            budget
        )

    def test_get_by_month_returns_none_when_not_found(
        self
    ) -> None:
        saved = self.repository.get_by_month(
            "2026-09"
        )

        self.assertIsNone(saved)

    def test_get_by_month_strips_spaces(
        self
    ) -> None:
        budget = Budget(
            month="2026-09",
            amount=500000,
        )

        self.repository.set(budget)

        saved = self.repository.get_by_month(
            " 2026-09 "
        )

        self.assertEqual(
            saved,
            budget
        )

    # --------------------------------------------------
    # iter_all
    # --------------------------------------------------

    def test_iter_all_returns_budgets_in_file_order(
        self
    ) -> None:
        september = Budget(
            month="2026-09",
            amount=500000,
        )

        october = Budget(
            month="2026-10",
            amount=600000,
        )

        self.repository.set(september)
        self.repository.set(october)

        budgets = list(
            self.repository.iter_all()
        )

        self.assertEqual(
            budgets,
            [
                september,
                october,
            ]
        )

    # --------------------------------------------------
    # 잘못된 JSONL
    # --------------------------------------------------

    def test_iter_all_invalid_json_raises_data_format_error(
        self
    ) -> None:
        self.file_path.write_text(
            "not json\n",
            encoding="utf-8"
        )

        with self.assertRaises(DataFormatError):
            list(
                self.repository.iter_all()
            )

    def test_iter_all_invalid_budget_data_raises_data_format_error(
        self
    ) -> None:
        self.file_path.write_text(
            '{"month": "2026-09"}\n',
            encoding="utf-8"
        )

        with self.assertRaises(DataFormatError):
            list(
                self.repository.iter_all()
            )



if __name__ == "__main__":
    unittest.main()