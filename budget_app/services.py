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
        if not self.category_repository.exists(category):
            raise NotFoundError(
                f"카테고리를 찾을 수 없습니다: {category}",
                hint="category add 명령으로 카테고리를 먼저 등록하세요."
            )
        
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
        
    # update_transaction()
    # delete_transaction()