from datetime import date as Date
from typing import Iterator

from budget_app.errors import NotFoundError
from budget_app.models import Transaction
from budget_app.repositories import (
    CategoryRepository,
    TransactionRepository
)
from budget_app.types import TransactionType

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