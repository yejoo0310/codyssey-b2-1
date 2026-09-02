from datetime import date as Date
from typing import Iterator

from budget_app.errors import CategoryInUseError
from budget_app.models import (
    Budget,
    Category, 
    MonthlySummary,
    Transaction,
)
from budget_app.repositories import (
    BudgetRepository,
    CategoryRepository,
    TransactionRepository
)
from budget_app.types import TransactionType
from budget_app.validators import parse_month, validate_positive_int

class TransactionService:
    def __init__(
        self,
        transaction_repository: TransactionRepository,
        category_repository: CategoryRepository
    ):
        self.transaction_repository = transaction_repository
        self.category_repository = category_repository
    
    def add_transaction(
        self,
        *,
        transaction_type: TransactionType,
        date: Date,
        amount: int,
        category: str,
        memo: str = "",
        tags: list[str] | None = None,
    ) -> Transaction:
        saved_category = self.category_repository.get_by_name(category)
        
        transaction_id = self.transaction_repository.generate_id()
        
        transaction = Transaction(
            id=transaction_id,
            type=transaction_type,
            date=date,
            amount=amount,
            category=category,
            memo=memo,
            tags=tags
        )
        
        self.transaction_repository.add(transaction)
        
        return transaction
        
    def list_transaction(
        self,
        *,
        limit: int = 20,
    ) -> Iterator[Transaction]:
        count = 0
        
        for transaction in self.transaction_repository.iter_all():
            if count >= limit:
                break
            
            yield transaction
            count += 1
            
    def search_transaction(
        self,
        *,
        date_from: Date | None = None,
        date_to: Date | None = None,
        category: str | None = None,
        transaction_type: TransactionType | None = None,
        query: str | None = None,
        tag: str | None = None,
    ) -> Iterator[Transaction]:
        for transaction in self.transaction_repository.iter_all():
            if date_from is not None and transaction.date < date_from:
                continue
            
            if date_to is not None and transaction.date > date_to:
                continue
            
            if category is not None and transaction.category != category.casefold():
                continue
                
            if transaction_type is not None and transaction.type != transaction_type:
                continue
            
            if query is not None and transaction.memo.casefold() != query.casefold:
                continue
            
            if (
                tag is not None
                and not any(
                    saved_tag.casefold() != tag.casefold()
                    for saved_tag in transaction.tags
                )
            ):
                continue
            
            yield transaction
        
    def update_transaction(
        self,
        transaction_id: str,
        *,
        transaction_type: TransactionType | None = None,
        date: Date | None = None,
        amount: int | None = None,
        category: str | None = None,
        memo: str | None = None,
        tags: list[str] | None = None,
    ) -> Transaction:
        transaction = self.transaction_repository.get_by_id(transaction_id)
        
        updated_category = transaction.category
        if category is not None:
            saved_category = self.category_repository.get_by_name(category)
            updated_category = saved_category.name
            
        updated = Transaction(
            id=transaction.id,
            type=(
                transaction_type
                if transaction_type is not None
                else transaction.type
            ),
            date=(
                date
                if date is not None
                else transaction.date
            ),
            amount=(
                amount
                if amount is not None
                else transaction.amount
            ),
            category=updated_category,
            memo=(
                memo
                if memo is not None
                else transaction.memo
            ),
            tags=(
                tags
                if tags is not None
                else transaction.tags.copy()
            )
        )
        
        self.transaction_repository.update(updated)
        
        return updated
        
    def delete_transaction(
        self,
        transaction_id: str,
    ) -> None:
        self.transaction_repository.delete(transaction_id)
        

class CategoryService:
    def __init__(
        self,
        category_repository: CategoryRepository,
        transaction_repository: TransactionRepository,
    ):
        self.category_repository = category_repository
        self.transaction_repository = transaction_repository
        
    def add_category(
        self,
        name: str
    ) -> Category:
        category = Category(name=name)
        self.category_repository.add(category)
        return category
    
    def list_category(self) -> Iterator[Category]:
        yield from self.category_repository.iter_all()

    def remove_category(
        self,
        name: str
    ) -> None:
        category = self.category_repository.get_by_name(name)
        
        for transaction in self.transaction_repository.iter_all():
            if transaction.category == category.name:
                raise CategoryInUseError(
                    f"사용 중인 카테고리는 삭제할 수 없습니다: {category.name}",
                    hint="해당 카테고리를 사용하는 거래를 먼저 수정하거나 삭제해 주세요."
                )
            
        self.category_repository.remove(category.name)


class BudgetService:
    def __init__(
        self,
        budget_repository: BudgetRepository
    ):
        self.budget_repository = budget_repository
        
    def set_budget(
        self,
        month: str,
        amount: int
    ) -> Budget:
        budget = Budget(
            month=month,
            amount=amount
        )
        
        self.budget_repository.set(budget)
        return budget
    
    def get_budget(
        self,
        month: str
    ) -> Budget:
        return self.budget_repository.get_by_month(month)
    

class SummaryService:
    def __init__(
        self,
        transaction_repository: TransactionRepository,
        budget_repository: BudgetRepository
    ):
        self.transaction_repository = transaction_repository
        self.budget_repository = budget_repository
       
    def get_monthly_summary(
        self,
        month: str
    ) -> MonthlySummary:
        month = parse_month(month)
        
        transaction_count = 0
        total_income = 0
        total_expense = 0
        
        for transaction in self.transaction_repository.iter_all():
            if transaction.date.strftime("%Y-%m") != month:
                continue
            
            transaction_count += 1
            
            if transaction.type == "income":
                total_income += transaction.amount
            else:
                total_expense += transaction.amount
                
        balance = total_income - total_expense
        
        saved_budget = self.budget_repository.get_by_month(month)
        
        if saved_budget is None:
            budget = None
            budget_usage_rate = None
            budget_exceeded = None
        else:
            budget = saved_budget.amount
            budget_usage_rate = total_expense / budget * 100
            budget_exceeded = total_expense > budget
        
        return MonthlySummary(
            month=month,
            transaction_count=transaction_count,
            total_income=total_income,
            total_expense=total_expense,
            balance=balance,
            budget=budget,
            budget_usage_rate=budget_usage_rate,
            budget_exceeded=budget_exceeded
        )
        
    def get_top_expense_categories(
        self,
        month: str,
        *,
        top: int = 3
    ) -> list[tuple[str, int]]:
        month = parse_month(month)
        validate_positive_int(top)
        
        category_expenses: dict[str, int] = {}
        
        for transaction in self.transaction_repository.iter_all():
            if transaction.date.strftime("%Y-%m") != month:
                continue
            
            if transaction.type != "expense":
                continue
            
            category_expenses[transaction.category] = (
                category_expenses.get(transaction.category, 0)
                + transaction.amount
            )
        
        sorted_categories = sorted(
            category_expenses.items(),
            key=lambda item: (-item[1], item[0]),
            reverse=True
        )
        
        return sorted_categories[:top]