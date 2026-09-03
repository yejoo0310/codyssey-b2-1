import csv
import tempfile
import unittest

from datetime import date
from pathlib import Path

from budget_app.errors import (
    CategoryInUseError,
    DataAccessError,
    DataFormatError,
    NotFoundError,
    ValidationError,
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
from budget_app.services import (
    BudgetService,
    CategoryService,
    ImportExportService,
    SummaryService,
    TransactionService,
)


# ============================================================
# TransactionService
# ============================================================

class TransactionServiceTest(unittest.TestCase):

    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        root = Path(self.temp_dir.name)

        self.transaction_repository = TransactionRepository(
            root / "transactions.jsonl"
        )

        self.category_repository = CategoryRepository(
            root / "categories.jsonl"
        )

        self.service = TransactionService(
            self.transaction_repository,
            self.category_repository,
        )

        self.category_repository.add(
            Category("food")
        )

        self.category_repository.add(
            Category("transport")
        )

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def add_transaction(
        self,
        *,
        transaction_type: str = "expense",
        transaction_date: date = date(2026, 9, 3),
        amount: int = 10000,
        category: str = "food",
        memo: str = "",
        tags: list[str] | None = None,
    ) -> Transaction:
        return self.service.add_transaction(
            transaction_type=transaction_type,
            date=transaction_date,
            amount=amount,
            category=category,
            memo=memo,
            tags=tags,
        )

    # --------------------------------------------------------
    # add_transaction
    # --------------------------------------------------------

    def test_add_transaction_saves_transaction(self) -> None:
        transaction = self.add_transaction(
            amount=15000,
            memo="점심",
            tags=["meal"],
        )

        self.assertEqual(
            transaction.id,
            "TX-000001",
        )

        self.assertTrue(
            self.transaction_repository.exists(
                "TX-000001"
            )
        )

        saved = self.transaction_repository.get_by_id(
            "TX-000001"
        )

        self.assertEqual(
            saved.amount,
            15000,
        )

        self.assertEqual(
            saved.memo,
            "점심",
        )

    def test_add_transaction_without_tags_uses_empty_list(
        self
    ) -> None:
        transaction = self.add_transaction(
            tags=None
        )

        self.assertEqual(
            transaction.tags,
            [],
        )

    def test_add_transaction_uses_normalized_category(
        self
    ) -> None:
        transaction = self.add_transaction(
            category=" FOOD "
        )

        self.assertEqual(
            transaction.category,
            "food",
        )

    def test_add_transaction_unknown_category_raises_not_found_error(
        self
    ) -> None:
        with self.assertRaises(NotFoundError):
            self.add_transaction(
                category="unknown"
            )

    def test_add_transaction_generates_next_id(
        self
    ) -> None:
        first = self.add_transaction()
        second = self.add_transaction()

        self.assertEqual(
            first.id,
            "TX-000001",
        )

        self.assertEqual(
            second.id,
            "TX-000002",
        )

    # --------------------------------------------------------
    # list_transaction
    # --------------------------------------------------------

    def test_list_transaction_respects_limit(
        self
    ) -> None:
        self.add_transaction(
            amount=10000
        )

        self.add_transaction(
            amount=20000
        )

        self.add_transaction(
            amount=30000
        )

        transactions = list(
            self.service.list_transaction(
                limit=2
            )
        )

        self.assertEqual(
            len(transactions),
            2,
        )

    def test_list_transaction_rejects_zero_limit(
        self
    ) -> None:
        with self.assertRaises(ValueError):
            list(
                self.service.list_transaction(
                    limit=0
                )
            )

    def test_list_transaction_rejects_negative_limit(
        self
    ) -> None:
        with self.assertRaises(ValueError):
            list(
                self.service.list_transaction(
                    limit=-1
                )
            )

    # --------------------------------------------------------
    # search_transaction
    # --------------------------------------------------------

    def test_search_transaction_by_date_from(
        self
    ) -> None:
        self.add_transaction(
            transaction_date=date(2026, 8, 31),
            amount=10000,
        )

        september = self.add_transaction(
            transaction_date=date(2026, 9, 3),
            amount=20000,
        )

        result = list(
            self.service.search_transaction(
                date_from=date(2026, 9, 1)
            )
        )

        self.assertEqual(
            result,
            [september],
        )

    def test_search_transaction_by_date_to(
        self
    ) -> None:
        august = self.add_transaction(
            transaction_date=date(2026, 8, 31)
        )

        self.add_transaction(
            transaction_date=date(2026, 9, 3)
        )

        result = list(
            self.service.search_transaction(
                date_to=date(2026, 8, 31)
            )
        )

        self.assertEqual(
            result,
            [august],
        )

    def test_search_transaction_by_date_range(
        self
    ) -> None:
        self.add_transaction(
            transaction_date=date(2026, 8, 31)
        )

        september = self.add_transaction(
            transaction_date=date(2026, 9, 10)
        )

        self.add_transaction(
            transaction_date=date(2026, 10, 1)
        )

        result = list(
            self.service.search_transaction(
                date_from=date(2026, 9, 1),
                date_to=date(2026, 9, 30),
            )
        )

        self.assertEqual(
            result,
            [september],
        )

    def test_search_transaction_by_category(
        self
    ) -> None:
        food = self.add_transaction(
            category="food"
        )

        self.add_transaction(
            category="transport"
        )

        result = list(
            self.service.search_transaction(
                category=" FOOD "
            )
        )

        self.assertEqual(
            result,
            [food],
        )

    def test_search_transaction_by_type(
        self
    ) -> None:
        self.add_transaction(
            transaction_type="income",
            amount=3000000,
        )

        expense = self.add_transaction(
            transaction_type="expense",
            amount=10000,
        )

        result = list(
            self.service.search_transaction(
                transaction_type="expense"
            )
        )

        self.assertEqual(
            result,
            [expense],
        )

    def test_search_transaction_by_memo_keyword(
        self
    ) -> None:
        target = self.add_transaction(
            memo="회사 근처에서 점심 식사"
        )

        self.add_transaction(
            memo="버스 요금"
        )

        result = list(
            self.service.search_transaction(
                query="점심"
            )
        )

        self.assertEqual(
            result,
            [target],
        )

    def test_search_transaction_memo_is_case_insensitive(
        self
    ) -> None:
        target = self.add_transaction(
            memo="Lunch With Team"
        )

        result = list(
            self.service.search_transaction(
                query="lunch"
            )
        )

        self.assertEqual(
            result,
            [target],
        )

    def test_search_transaction_by_tag(
        self
    ) -> None:
        target = self.add_transaction(
            tags=[
                "meal",
                "company",
            ]
        )

        self.add_transaction(
            tags=["transport"]
        )

        result = list(
            self.service.search_transaction(
                tag="meal"
            )
        )

        self.assertEqual(
            result,
            [target],
        )

    def test_search_transaction_tag_is_case_insensitive(
        self
    ) -> None:
        target = self.add_transaction(
            tags=["Meal"]
        )

        result = list(
            self.service.search_transaction(
                tag="meal"
            )
        )

        self.assertEqual(
            result,
            [target],
        )

    def test_search_transaction_combines_conditions(
        self
    ) -> None:
        target = self.add_transaction(
            transaction_type="expense",
            transaction_date=date(2026, 9, 3),
            category="food",
            memo="회사 점심",
            tags=["meal"],
        )

        self.add_transaction(
            transaction_type="expense",
            transaction_date=date(2026, 9, 3),
            category="transport",
            memo="회사 버스",
            tags=["transport"],
        )

        result = list(
            self.service.search_transaction(
                date_from=date(2026, 9, 1),
                date_to=date(2026, 9, 30),
                category="food",
                transaction_type="expense",
                query="점심",
                tag="meal",
            )
        )

        self.assertEqual(
            result,
            [target],
        )

    # --------------------------------------------------------
    # update_transaction
    # --------------------------------------------------------

    def test_update_transaction_changes_selected_fields(
        self
    ) -> None:
        original = self.add_transaction(
            amount=10000,
            memo="기존 메모",
            tags=["old"],
        )

        updated = self.service.update_transaction(
            original.id,
            amount=50000,
            memo="수정된 메모",
        )

        self.assertEqual(
            updated.amount,
            50000,
        )

        self.assertEqual(
            updated.memo,
            "수정된 메모",
        )

        self.assertEqual(
            updated.category,
            "food",
        )

        self.assertEqual(
            updated.tags,
            ["old"],
        )

    def test_update_transaction_can_change_category(
        self
    ) -> None:
        original = self.add_transaction(
            category="food"
        )

        updated = self.service.update_transaction(
            original.id,
            category="transport",
        )

        self.assertEqual(
            updated.category,
            "transport",
        )

    def test_update_transaction_unknown_category_raises_not_found_error(
        self
    ) -> None:
        original = self.add_transaction()

        with self.assertRaises(NotFoundError):
            self.service.update_transaction(
                original.id,
                category="unknown",
            )

    def test_update_missing_transaction_raises_not_found_error(
        self
    ) -> None:
        with self.assertRaises(NotFoundError):
            self.service.update_transaction(
                "TX-999999",
                amount=50000,
            )

    # --------------------------------------------------------
    # delete_transaction
    # --------------------------------------------------------

    def test_delete_transaction(
        self
    ) -> None:
        transaction = self.add_transaction()

        self.service.delete_transaction(
            transaction.id
        )

        self.assertFalse(
            self.transaction_repository.exists(
                transaction.id
            )
        )

    def test_delete_missing_transaction_raises_not_found_error(
        self
    ) -> None:
        with self.assertRaises(NotFoundError):
            self.service.delete_transaction(
                "TX-999999"
            )


# ============================================================
# CategoryService
# ============================================================

class CategoryServiceTest(unittest.TestCase):

    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        root = Path(self.temp_dir.name)

        self.transaction_repository = TransactionRepository(
            root / "transactions.jsonl"
        )

        self.category_repository = CategoryRepository(
            root / "categories.jsonl"
        )

        self.service = CategoryService(
            self.category_repository,
            self.transaction_repository,
        )

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def test_add_category(
        self
    ) -> None:
        category = self.service.add_category(
            " FOOD "
        )

        self.assertEqual(
            category.name,
            "food",
        )

        self.assertTrue(
            self.category_repository.exists(
                "food"
            )
        )

    def test_list_category(
        self
    ) -> None:
        self.service.add_category(
            "food"
        )

        self.service.add_category(
            "transport"
        )

        result = list(
            self.service.list_category()
        )

        self.assertEqual(
            [
                category.name
                for category in result
            ],
            [
                "food",
                "transport",
            ]
        )

    def test_remove_category(
        self
    ) -> None:
        self.service.add_category(
            "food"
        )

        self.service.remove_category(
            "food"
        )

        self.assertFalse(
            self.category_repository.exists(
                "food"
            )
        )

    def test_remove_category_in_use_raises_category_in_use_error(
        self
    ) -> None:
        self.service.add_category(
            "food"
        )

        self.transaction_repository.add(
            Transaction(
                id="TX-000001",
                type="expense",
                date=date(2026, 9, 3),
                amount=10000,
                category="food",
            )
        )

        with self.assertRaises(
            CategoryInUseError
        ):
            self.service.remove_category(
                "food"
            )

        self.assertTrue(
            self.category_repository.exists(
                "food"
            )
        )

    def test_remove_missing_category_raises_not_found_error(
        self
    ) -> None:
        with self.assertRaises(NotFoundError):
            self.service.remove_category(
                "unknown"
            )


# ============================================================
# BudgetService
# ============================================================

class BudgetServiceTest(unittest.TestCase):

    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        root = Path(self.temp_dir.name)

        self.budget_repository = BudgetRepository(
            root / "budgets.jsonl"
        )

        self.service = BudgetService(
            self.budget_repository
        )

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def test_set_budget(
        self
    ) -> None:
        budget = self.service.set_budget(
            "2026-09",
            500000,
        )

        self.assertEqual(
            budget.month,
            "2026-09",
        )

        self.assertEqual(
            budget.amount,
            500000,
        )

    def test_set_budget_replaces_existing_budget(
        self
    ) -> None:
        self.service.set_budget(
            "2026-09",
            500000,
        )

        self.service.set_budget(
            "2026-09",
            700000,
        )

        saved = self.service.get_budget(
            "2026-09"
        )

        self.assertIsNotNone(saved)

        self.assertEqual(
            saved.amount,
            700000,
        )

    def test_get_budget_returns_none_when_not_found(
        self
    ) -> None:
        budget = self.service.get_budget(
            "2026-09"
        )

        self.assertIsNone(
            budget
        )


# ============================================================
# SummaryService
# ============================================================

class SummaryServiceTest(unittest.TestCase):

    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        root = Path(self.temp_dir.name)

        self.transaction_repository = TransactionRepository(
            root / "transactions.jsonl"
        )

        self.budget_repository = BudgetRepository(
            root / "budgets.jsonl"
        )

        self.service = SummaryService(
            self.transaction_repository,
            self.budget_repository,
        )

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def add_transaction(
        self,
        transaction_id: str,
        *,
        transaction_type: str,
        amount: int,
        category: str,
        transaction_date: date = date(2026, 9, 3),
    ) -> None:
        self.transaction_repository.add(
            Transaction(
                id=transaction_id,
                type=transaction_type,
                date=transaction_date,
                amount=amount,
                category=category,
            )
        )

    # --------------------------------------------------------
    # monthly summary
    # --------------------------------------------------------

    def test_get_monthly_summary(
        self
    ) -> None:
        self.add_transaction(
            "TX-000001",
            transaction_type="income",
            amount=3000000,
            category="salary",
        )

        self.add_transaction(
            "TX-000002",
            transaction_type="expense",
            amount=100000,
            category="food",
        )

        self.add_transaction(
            "TX-000003",
            transaction_type="expense",
            amount=50000,
            category="transport",
        )

        summary = self.service.get_monthly_summary(
            "2026-09"
        )

        self.assertEqual(
            summary.transaction_count,
            3,
        )

        self.assertEqual(
            summary.total_income,
            3000000,
        )

        self.assertEqual(
            summary.total_expense,
            150000,
        )

        self.assertEqual(
            summary.balance,
            2850000,
        )

    def test_monthly_summary_ignores_other_months(
        self
    ) -> None:
        self.add_transaction(
            "TX-000001",
            transaction_type="expense",
            amount=10000,
            category="food",
            transaction_date=date(2026, 9, 3),
        )

        self.add_transaction(
            "TX-000002",
            transaction_type="expense",
            amount=50000,
            category="food",
            transaction_date=date(2026, 10, 3),
        )

        summary = self.service.get_monthly_summary(
            "2026-09"
        )

        self.assertEqual(
            summary.transaction_count,
            1,
        )

        self.assertEqual(
            summary.total_expense,
            10000,
        )

    def test_monthly_summary_without_budget(
        self
    ) -> None:
        summary = self.service.get_monthly_summary(
            "2026-09"
        )

        self.assertIsNone(
            summary.budget
        )

        self.assertIsNone(
            summary.budget_usage_rate
        )

        self.assertIsNone(
            summary.budget_exceeded
        )

    def test_monthly_summary_with_budget(
        self
    ) -> None:
        self.add_transaction(
            "TX-000001",
            transaction_type="expense",
            amount=150000,
            category="food",
        )

        self.budget_repository.set(
            Budget(
                month="2026-09",
                amount=500000,
            )
        )

        summary = self.service.get_monthly_summary(
            "2026-09"
        )

        self.assertEqual(
            summary.budget,
            500000,
        )

        self.assertEqual(
            summary.budget_usage_rate,
            30.0,
        )

        self.assertFalse(
            summary.budget_exceeded
        )

    def test_monthly_summary_budget_exceeded(
        self
    ) -> None:
        self.add_transaction(
            "TX-000001",
            transaction_type="expense",
            amount=600000,
            category="food",
        )

        self.budget_repository.set(
            Budget(
                month="2026-09",
                amount=500000,
            )
        )

        summary = self.service.get_monthly_summary(
            "2026-09"
        )

        self.assertTrue(
            summary.budget_exceeded
        )

        self.assertEqual(
            summary.budget_usage_rate,
            120.0,
        )

    def test_monthly_summary_invalid_month_raises_value_error(
        self
    ) -> None:
        with self.assertRaises(ValueError):
            self.service.get_monthly_summary(
                "2026-13"
            )

    # --------------------------------------------------------
    # top expense categories
    # --------------------------------------------------------

    def test_get_top_expense_categories(
        self
    ) -> None:
        self.add_transaction(
            "TX-000001",
            transaction_type="expense",
            amount=100000,
            category="food",
        )

        self.add_transaction(
            "TX-000002",
            transaction_type="expense",
            amount=50000,
            category="food",
        )

        self.add_transaction(
            "TX-000003",
            transaction_type="expense",
            amount=200000,
            category="rent",
        )

        self.add_transaction(
            "TX-000004",
            transaction_type="expense",
            amount=20000,
            category="transport",
        )

        result = (
            self.service
            .get_top_expense_categories(
                "2026-09"
            )
        )

        self.assertEqual(
            result,
            [
                ("rent", 200000),
                ("food", 150000),
                ("transport", 20000),
            ]
        )

    def test_get_top_expense_categories_respects_top(
        self
    ) -> None:
        self.add_transaction(
            "TX-000001",
            transaction_type="expense",
            amount=100000,
            category="food",
        )

        self.add_transaction(
            "TX-000002",
            transaction_type="expense",
            amount=200000,
            category="rent",
        )

        self.add_transaction(
            "TX-000003",
            transaction_type="expense",
            amount=50000,
            category="transport",
        )

        result = (
            self.service
            .get_top_expense_categories(
                "2026-09",
                top=2,
            )
        )

        self.assertEqual(
            len(result),
            2,
        )

        self.assertEqual(
            result,
            [
                ("rent", 200000),
                ("food", 100000),
            ]
        )

    def test_top_expense_categories_ignores_income(
        self
    ) -> None:
        self.add_transaction(
            "TX-000001",
            transaction_type="income",
            amount=3000000,
            category="salary",
        )

        self.add_transaction(
            "TX-000002",
            transaction_type="expense",
            amount=100000,
            category="food",
        )

        result = (
            self.service
            .get_top_expense_categories(
                "2026-09"
            )
        )

        self.assertEqual(
            result,
            [
                ("food", 100000),
            ]
        )

    def test_top_expense_categories_same_amount_sorted_by_name(
        self
    ) -> None:
        self.add_transaction(
            "TX-000001",
            transaction_type="expense",
            amount=100000,
            category="transport",
        )

        self.add_transaction(
            "TX-000002",
            transaction_type="expense",
            amount=100000,
            category="food",
        )

        result = (
            self.service
            .get_top_expense_categories(
                "2026-09"
            )
        )

        self.assertEqual(
            result,
            [
                ("food", 100000),
                ("transport", 100000),
            ]
        )

    def test_top_zero_raises_value_error(
        self
    ) -> None:
        with self.assertRaises(ValueError):
            self.service.get_top_expense_categories(
                "2026-09",
                top=0,
            )


# ============================================================
# ImportExportService
# ============================================================

class ImportExportServiceTest(unittest.TestCase):

    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.root = Path(
            self.temp_dir.name
        )

        self.transaction_repository = TransactionRepository(
            self.root / "transactions.jsonl"
        )

        self.category_repository = CategoryRepository(
            self.root / "categories.jsonl"
        )

        self.service = ImportExportService(
            self.transaction_repository,
            self.category_repository,
        )

        self.category_repository.add(
            Category("food")
        )

        self.category_repository.add(
            Category("transport")
        )

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    # --------------------------------------------------------
    # import
    # --------------------------------------------------------

    def test_import_csv(
        self
    ) -> None:
        csv_path = (
            self.root
            / "import.csv"
        )

        csv_path.write_text(
            (
                "date,type,category,amount,memo,tags\n"
                "2026-09-01,expense,food,10000,점심,meal\n"
                "2026-09-02,expense,transport,20000,버스,commute\n"
            ),
            encoding="utf-8",
        )

        result = self.service.import_csv(
            csv_path
        )

        self.assertEqual(
            result.imported,
            2,
        )

        self.assertEqual(
            result.skipped,
            0,
        )

        transactions = list(
            self.transaction_repository.iter_all()
        )

        self.assertEqual(
            len(transactions),
            2,
        )

    def test_import_csv_skips_invalid_row(
        self
    ) -> None:
        csv_path = (
            self.root
            / "import.csv"
        )

        csv_path.write_text(
            (
                "date,type,category,amount,memo,tags\n"
                "2026-09-01,expense,food,10000,점심,meal\n"
                "2026-09-02,expense,food,-100,잘못된 금액,bad\n"
            ),
            encoding="utf-8",
        )

        result = self.service.import_csv(
            csv_path
        )

        self.assertEqual(
            result.imported,
            1,
        )

        self.assertEqual(
            result.skipped,
            1,
        )

    def test_import_csv_skips_unknown_category(
        self
    ) -> None:
        csv_path = (
            self.root
            / "import.csv"
        )

        csv_path.write_text(
            (
                "date,type,category,amount,memo,tags\n"
                "2026-09-01,expense,unknown,10000,점심,meal\n"
            ),
            encoding="utf-8",
        )

        result = self.service.import_csv(
            csv_path
        )

        self.assertEqual(
            result.imported,
            0,
        )

        self.assertEqual(
            result.skipped,
            1,
        )

    def test_import_csv_ignores_blank_rows(
        self
    ) -> None:
        csv_path = (
            self.root
            / "import.csv"
        )

        csv_path.write_text(
            (
                "date,type,category,amount,memo,tags\n"
                "2026-09-01,expense,food,10000,점심,meal\n"
                ",,,,,\n"
            ),
            encoding="utf-8",
        )

        result = self.service.import_csv(
            csv_path
        )

        self.assertEqual(
            result.imported,
            1,
        )

        self.assertEqual(
            result.skipped,
            0,
        )

    def test_import_csv_missing_required_column_raises_data_format_error(
        self
    ) -> None:
        csv_path = (
            self.root
            / "import.csv"
        )

        csv_path.write_text(
            (
                "date,type,category,memo\n"
                "2026-09-01,expense,food,점심\n"
            ),
            encoding="utf-8",
        )

        with self.assertRaises(
            DataFormatError
        ):
            self.service.import_csv(
                csv_path
            )

    def test_import_missing_file_raises_data_access_error(
        self
    ) -> None:
        missing_path = (
            self.root
            / "missing.csv"
        )

        with self.assertRaises(
            DataAccessError
        ):
            self.service.import_csv(
                missing_path
            )

    # --------------------------------------------------------
    # export
    # --------------------------------------------------------

    def add_saved_transaction(
        self,
        transaction_id: str,
        *,
        transaction_date: date,
        amount: int,
        category: str = "food",
        memo: str = "",
        tags: list[str] | None = None,
    ) -> None:
        self.transaction_repository.add(
            Transaction(
                id=transaction_id,
                type="expense",
                date=transaction_date,
                amount=amount,
                category=category,
                memo=memo,
                tags=(
                    tags
                    if tags is not None
                    else []
                ),
            )
        )

    def test_export_csv_by_month(
        self
    ) -> None:
        self.add_saved_transaction(
            "TX-000001",
            transaction_date=date(
                2026, 9, 1
            ),
            amount=10000,
        )

        self.add_saved_transaction(
            "TX-000002",
            transaction_date=date(
                2026, 9, 20
            ),
            amount=20000,
        )

        self.add_saved_transaction(
            "TX-000003",
            transaction_date=date(
                2026, 10, 1
            ),
            amount=30000,
        )

        output_path = (
            self.root
            / "export.csv"
        )

        exported = self.service.export_csv(
            output_path,
            month="2026-09",
        )

        self.assertEqual(
            exported,
            2,
        )

        self.assertTrue(
            output_path.exists()
        )

        with output_path.open(
            "r",
            encoding="utf-8",
            newline="",
        ) as file:
            rows = list(
                csv.DictReader(file)
            )

        self.assertEqual(
            len(rows),
            2,
        )

        self.assertEqual(
            rows[1]["amount"],
            "10000",
        )

        self.assertEqual(
            rows[0]["amount"],
            "20000",
        )

    def test_export_csv_by_date_range(
        self
    ) -> None:
        self.add_saved_transaction(
            "TX-000001",
            transaction_date=date(
                2026, 8, 31
            ),
            amount=10000,
        )

        self.add_saved_transaction(
            "TX-000002",
            transaction_date=date(
                2026, 9, 10
            ),
            amount=20000,
        )

        self.add_saved_transaction(
            "TX-000003",
            transaction_date=date(
                2026, 10, 1
            ),
            amount=30000,
        )

        output_path = (
            self.root
            / "export.csv"
        )

        exported = self.service.export_csv(
            output_path,
            date_from=date(
                2026, 9, 1
            ),
            date_to=date(
                2026, 9, 30
            ),
        )

        self.assertEqual(
            exported,
            1,
        )

        with output_path.open(
            "r",
            encoding="utf-8",
            newline="",
        ) as file:
            rows = list(
                csv.DictReader(file)
            )

        self.assertEqual(
            len(rows),
            1,
        )

        self.assertEqual(
            rows[0]["amount"],
            "20000",
        )

    def test_export_csv_writes_optional_fields(
        self
    ) -> None:
        self.add_saved_transaction(
            "TX-000001",
            transaction_date=date(
                2026, 9, 1
            ),
            amount=10000,
            memo="점심",
            tags=[
                "meal",
                "company",
            ],
        )

        output_path = (
            self.root
            / "export.csv"
        )

        self.service.export_csv(
            output_path,
            month="2026-09",
        )

        with output_path.open(
            "r",
            encoding="utf-8",
            newline="",
        ) as file:
            rows = list(
                csv.DictReader(file)
            )

        self.assertEqual(
            rows[0]["memo"],
            "점심",
        )

        self.assertEqual(
            rows[0]["tags"],
            "meal,company",
        )

    def test_export_creates_parent_directories(
        self
    ) -> None:
        self.add_saved_transaction(
            "TX-000001",
            transaction_date=date(
                2026, 9, 1
            ),
            amount=10000,
        )

        output_path = (
            self.root
            / "exports"
            / "2026"
            / "export.csv"
        )

        self.service.export_csv(
            output_path,
            month="2026-09",
        )

        self.assertTrue(
            output_path.exists()
        )

    def test_export_without_filter_raises_validation_error(
        self
    ) -> None:
        output_path = (
            self.root
            / "export.csv"
        )

        with self.assertRaises(
            ValidationError
        ):
            self.service.export_csv(
                output_path
            )

    def test_export_month_and_date_range_together_raises_validation_error(
        self
    ) -> None:
        output_path = (
            self.root
            / "export.csv"
        )

        with self.assertRaises(
            ValidationError
        ):
            self.service.export_csv(
                output_path,
                month="2026-09",
                date_from=date(
                    2026, 9, 1
                ),
                date_to=date(
                    2026, 9, 30
                ),
            )

    def test_export_only_start_date_raises_validation_error(
        self
    ) -> None:
        output_path = (
            self.root
            / "export.csv"
        )

        with self.assertRaises(
            ValidationError
        ):
            self.service.export_csv(
                output_path,
                date_from=date(
                    2026, 9, 1
                ),
            )

    def test_export_invalid_month_raises_validation_error(
        self
    ) -> None:
        output_path = (
            self.root
            / "export.csv"
        )

        with self.assertRaises(
            ValidationError
        ):
            self.service.export_csv(
                output_path,
                month="2026-13",
            )


if __name__ == "__main__":
    unittest.main()