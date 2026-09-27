from dataclasses import dataclass
from pathlib import Path

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


@dataclass(slots=True)
class Services:
    transaction: TransactionService
    category: CategoryService
    budget: BudgetService
    summary: SummaryService
    import_export: ImportExportService


def build_services(data_dir: Path) -> Services:
    transaction_repository = TransactionRepository(
        data_dir / "transactions.jsonl"
    )

    category_repository = CategoryRepository(
        data_dir / "categories.jsonl"
    )

    budget_repository = BudgetRepository(
        data_dir / "budgets.jsonl"
    )

    return Services(
        transaction=TransactionService(
            transaction_repository,
            category_repository,
        ),
        category=CategoryService(
            category_repository,
            transaction_repository,
        ),
        budget=BudgetService(
            budget_repository,
        ),
        summary=SummaryService(
            transaction_repository,
            budget_repository,
        ),
        import_export=ImportExportService(
            transaction_repository,
            category_repository,
        ),
    )