import unittest
from datetime import date as Date
from pathlib import Path
from tempfile import TemporaryDirectory

from budget_app.errors import (
    DataFormatError,
    DuplicateError,
    NotFoundError,
)
from budget_app.models import Budget, Category, Transaction
from budget_app.repositories import (
    BudgetRepository,
    CategoryRepository,
    JsonlRepository,
    TransactionRepository,
)


class TemporaryRepositoryTestCase(unittest.TestCase):
    """각 테스트에서 사용할 임시 저장 디렉터리를 준비한다."""

    def setUp(self) -> None:
        self.temp_directory = TemporaryDirectory()
        self.data_dir = Path(self.temp_directory.name)

    def tearDown(self) -> None:
        self.temp_directory.cleanup()

    def make_path(self, filename: str) -> Path:
        return self.data_dir / filename


class JsonlRepositoryTest(TemporaryRepositoryTestCase):
    def test_repository_creates_parent_directory_and_file(self) -> None:
        file_path = self.data_dir / "nested" / "records.jsonl"

        JsonlRepository(file_path)

        self.assertTrue(file_path.parent.exists())
        self.assertTrue(file_path.exists())
        self.assertTrue(file_path.is_file())

    def test_iter_dicts_reads_records_in_file_order(self) -> None:
        file_path = self.make_path("records.jsonl")
        repository = JsonlRepository(file_path)

        repository._append_dict({"id": "A"})
        repository._append_dict({"id": "B"})

        records = list(repository._iter_dicts())

        self.assertEqual(
            records,
            [
                {"id": "A"},
                {"id": "B"},
            ],
        )

    def test_iter_dicts_ignores_empty_lines(self) -> None:
        file_path = self.make_path("records.jsonl")
        file_path.write_text(
            '{"id": "A"}\n'
            "\n"
            "   \n"
            '{"id": "B"}\n',
            encoding="utf-8",
        )

        repository = JsonlRepository(file_path)

        self.assertEqual(
            list(repository._iter_dicts()),
            [
                {"id": "A"},
                {"id": "B"},
            ],
        )

    def test_invalid_json_raises_data_format_error(self) -> None:
        file_path = self.make_path("records.jsonl")
        file_path.write_text(
            '{"id": "A"}\n'
            '{"id": 잘못된 JSON}\n',
            encoding="utf-8",
        )

        repository = JsonlRepository(file_path)

        with self.assertRaises(DataFormatError):
            list(repository._iter_dicts())

    def test_non_object_json_raises_data_format_error(self) -> None:
        file_path = self.make_path("records.jsonl")
        file_path.write_text(
            '["A", "B"]\n',
            encoding="utf-8",
        )

        repository = JsonlRepository(file_path)

        with self.assertRaises(DataFormatError):
            list(repository._iter_dicts())

    def test_rewrite_failure_preserves_original_file(self) -> None:
        file_path = self.make_path("records.jsonl")
        original_content = (
            '{"id": "A"}\n'
            '{"id": "B"}\n'
        )
        file_path.write_text(
            original_content,
            encoding="utf-8",
        )

        repository = JsonlRepository(file_path)

        invalid_records = [
            {"id": "changed"},
            {
                "id": "invalid",
                "date": Date(2026, 8, 6),
            },
        ]

        with self.assertRaises(DataFormatError):
            repository._rewrite_dicts(invalid_records)

        self.assertEqual(
            file_path.read_text(encoding="utf-8"),
            original_content,
        )


class TransactionRepositoryTest(TemporaryRepositoryTestCase):
    def setUp(self) -> None:
        super().setUp()

        self.file_path = self.make_path("transactions.jsonl")
        self.repository = TransactionRepository(self.file_path)

    @staticmethod
    def make_transaction(
        transaction_id: str,
        *,
        amount: int = 15_000,
        memo: str = "점심",
    ) -> Transaction:
        return Transaction(
            id=transaction_id,
            type="expense",
            date=Date(2026, 8, 6),
            amount=amount,
            category="food",
            memo=memo,
            tags=["meal"],
        )

    def test_add_and_iter_all(self) -> None:
        first = self.make_transaction("TX-001")
        second = self.make_transaction(
            "TX-002",
            amount=20_000,
        )

        self.repository.add(first)
        self.repository.add(second)

        self.assertEqual(
            list(self.repository.iter_all()),
            [first, second],
        )

    def test_get_by_id_and_exists(self) -> None:
        transaction = self.make_transaction("TX-001")
        self.repository.add(transaction)

        self.assertEqual(
            self.repository.get_by_id("TX-001"),
            transaction,
        )
        self.assertTrue(
            self.repository.exists("TX-001")
        )
        self.assertFalse(
            self.repository.exists("TX-999")
        )

    def test_get_missing_id_raises_not_found_error(self) -> None:
        with self.assertRaises(NotFoundError):
            self.repository.get_by_id("TX-999")

    def test_duplicate_id_raises_duplicate_error(self) -> None:
        transaction = self.make_transaction("TX-001")

        self.repository.add(transaction)

        with self.assertRaises(DuplicateError):
            self.repository.add(transaction)

        self.assertEqual(
            len(list(self.repository.iter_all())),
            1,
        )

    def test_update_replaces_only_matching_transaction(self) -> None:
        first = self.make_transaction("TX-001")
        second = self.make_transaction(
            "TX-002",
            amount=20_000,
        )

        self.repository.add(first)
        self.repository.add(second)

        updated = self.make_transaction(
            "TX-001",
            amount=30_000,
            memo="수정된 거래",
        )

        self.repository.update(updated)

        self.assertEqual(
            self.repository.get_by_id("TX-001"),
            updated,
        )
        self.assertEqual(
            self.repository.get_by_id("TX-002"),
            second,
        )

    def test_update_missing_transaction_raises_not_found_error(
        self,
    ) -> None:
        missing = self.make_transaction("TX-999")

        with self.assertRaises(NotFoundError):
            self.repository.update(missing)

    def test_delete_removes_only_matching_transaction(self) -> None:
        first = self.make_transaction("TX-001")
        second = self.make_transaction("TX-002")

        self.repository.add(first)
        self.repository.add(second)

        self.repository.delete("TX-001")

        self.assertFalse(
            self.repository.exists("TX-001")
        )
        self.assertEqual(
            list(self.repository.iter_all()),
            [second],
        )

    def test_delete_missing_transaction_raises_not_found_error(
        self,
    ) -> None:
        with self.assertRaises(NotFoundError):
            self.repository.delete("TX-999")

    def test_invalid_transaction_record_raises_data_format_error(
        self,
    ) -> None:
        self.file_path.write_text(
            '{"id": "TX-001", "amount": 15000}\n',
            encoding="utf-8",
        )

        with self.assertRaises(DataFormatError):
            list(self.repository.iter_all())


class CategoryRepositoryTest(TemporaryRepositoryTestCase):
    def setUp(self) -> None:
        super().setUp()

        self.file_path = self.make_path("categories.jsonl")
        self.repository = CategoryRepository(self.file_path)

    def test_add_and_iter_all(self) -> None:
        food = Category(name="food")
        transport = Category(name="transport")

        self.repository.add(food)
        self.repository.add(transport)

        self.assertEqual(
            list(self.repository.iter_all()),
            [food, transport],
        )

    def test_get_by_name_and_exists(self) -> None:
        category = Category(name="food")
        self.repository.add(category)

        self.assertEqual(
            self.repository.get_by_name("food"),
            category,
        )
        self.assertTrue(
            self.repository.exists("food")
        )
        self.assertTrue(
            self.repository.exists("  food  ")
        )
        self.assertFalse(
            self.repository.exists("rent")
        )

    def test_duplicate_category_raises_duplicate_error(
        self,
    ) -> None:
        self.repository.add(Category(name="food"))

        with self.assertRaises(DuplicateError):
            self.repository.add(Category(name="food"))

        self.assertEqual(
            len(list(self.repository.iter_all())),
            1,
        )

    def test_remove_category(self) -> None:
        food = Category(name="food")
        transport = Category(name="transport")

        self.repository.add(food)
        self.repository.add(transport)

        self.repository.remove("food")

        self.assertFalse(
            self.repository.exists("food")
        )
        self.assertEqual(
            list(self.repository.iter_all()),
            [transport],
        )

    def test_remove_missing_category_raises_not_found_error(
        self,
    ) -> None:
        with self.assertRaises(NotFoundError):
            self.repository.remove("rent")

    def test_invalid_category_record_raises_data_format_error(
        self,
    ) -> None:
        self.file_path.write_text(
            '{"category": "food"}\n',
            encoding="utf-8",
        )

        with self.assertRaises(DataFormatError):
            list(self.repository.iter_all())


class BudgetRepositoryTest(TemporaryRepositoryTestCase):
    def setUp(self) -> None:
        super().setUp()

        self.file_path = self.make_path("budgets.jsonl")
        self.repository = BudgetRepository(self.file_path)

    def test_set_adds_new_budget(self) -> None:
        budget = Budget(
            month="2026-08",
            amount=500_000,
        )

        self.repository.set(budget)

        self.assertEqual(
            self.repository.get_by_month("2026-08"),
            budget,
        )
        self.assertTrue(
            self.repository.exists("2026-08")
        )

    def test_set_updates_existing_month(self) -> None:
        original = Budget(
            month="2026-08",
            amount=500_000,
        )
        updated = Budget(
            month="2026-08",
            amount=650_000,
        )

        self.repository.set(original)
        self.repository.set(updated)

        self.assertEqual(
            self.repository.get_by_month("2026-08"),
            updated,
        )
        self.assertEqual(
            len(list(self.repository.iter_all())),
            1,
        )

    def test_set_keeps_other_months(self) -> None:
        july = Budget(
            month="2026-07",
            amount=400_000,
        )
        august = Budget(
            month="2026-08",
            amount=500_000,
        )

        self.repository.set(july)
        self.repository.set(august)

        updated_august = Budget(
            month="2026-08",
            amount=700_000,
        )
        self.repository.set(updated_august)

        self.assertEqual(
            list(self.repository.iter_all()),
            [july, updated_august],
        )

    def test_missing_month_returns_none(self) -> None:
        self.assertIsNone(
            self.repository.get_by_month("2026-12")
        )
        self.assertFalse(
            self.repository.exists("2026-12")
        )

    def test_invalid_budget_record_raises_data_format_error(
        self,
    ) -> None:
        self.file_path.write_text(
            '{"month": "2026-99", "amount": 500000}\n',
            encoding="utf-8",
        )

        with self.assertRaises(DataFormatError):
            list(self.repository.iter_all())


if __name__ == "__main__":
    unittest.main()