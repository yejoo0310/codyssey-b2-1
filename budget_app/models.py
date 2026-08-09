import re

from dataclasses import dataclass, field
from datetime import date as Date
from typing import Any

from budget_app.validators import (
    normalize_optional_text,
    normalize_required_text,
    normalize_tags,
    parse_date,
    parse_month,
    parse_positive_int,
    parsed_tags,
    parse_transaction_type,
    validate_date,
    validate_month,
    validate_positive_int,
    validate_transaction_type
)

from budget_app.types import TransactionType


"""수입/지출 거래 한 건을 나타내는 데이터 모델"""
@dataclass(slots=True)
class Transaction:
    id: str
    type: TransactionType
    date: Date
    amount: int
    category: str
    memo: str = ""
    tags: list[str] = field(default_factory=list)

    """모든 생성 경로에서 객체의 최종 상태를 검증"""
    def __post_init__(self) -> None:
        self.id = normalize_required_text(
            self.id,
            "거래 ID"
        )
        self.category = normalize_required_text(
            self.category,
            "카테고리"
        )
        self.memo = normalize_optional_text(
            self.memo,
            "메모"
        )
        
        self.type = validate_transaction_type(
            self.type,
            "거래 유형"
        )
        
        self.date = validate_date(
            self.date,
            "거래 날짜"
        )
        
        self.amount = validate_positive_int(
            self.amount,
            "거래 금액"
        )

        self.tags = normalize_tags(self.tags)


    """JSONL에 저장할 수 있는 딕셔너리로 변환"""
    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "type": self.type,
            "date": self.date.isoformat(),
            "amount": self.amount,
            "category": self.category,
            "memo": self.memo,
            "tags": self.tags.copy()
        }


    """JSONL에서 읽은 딕셔너리(외부 저장 데이터)를 내부 자료형으로 변환"""
    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Transaction":
        try:
            return cls(
                id=normalize_required_text(
                    data["id"],
                    "거래 ID"
                ),
                type=parse_transaction_type(
                    data["type"],
                    "거래 유형"
                ),
                date=parse_date(
                    data["date"],
                    "거래 날짜"
                ),
                amount=parse_positive_int(
                    data["amount"],
                    "거래 금액"
                ),
                category=normalize_required_text(
                    data["category"],
                    "카테고리"
                ),
                memo=normalize_optional_text(
                    data.get("memo", ""),
                    "메모"
                ),
                tags=parsed_tags(data.get("tags", []))
            )
        except KeyError as error:
            missing_field = error.args[0];
            raise ValueError(f"거래 데이터에 필수 필드가 없습니다: {missing_field}") from error
    
    
"""특정 월에 설정된 예산을 나타내는 데이터 모델"""
@dataclass(slots=True)
class Budget:
    month: str
    amount: int
    
    def __post_init__(self) -> None:
        self.month = validate_month(
            self.month,
            "예산 월"
        )
        
        self.amount = validate_positive_int(
            self.amount,
            "예산 금액"
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "month": self.month,
            "amount": self.amount
        }
        
    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Budget":
        try:
            return cls(
                month=parse_month(
                    data["month"],
                    "예산 월"    
                ),
                amount=parse_positive_int(
                    data["amount"],
                    "예산 금액"
                ) 
            )
        except KeyError as error:
            missing_field = error.args[0]

            raise ValueError(f"예산 데이터에 필수 필드가 없습니다 : {missing_field}") from error
    
    
"""거래에 사용할 카테고리를 나타내는 데이터 모델"""
@dataclass(slots=True, frozen=True)
class Category:
    name: str
    
    def __post_init__(self) -> None:
        normalized_name = normalize_required_text(self.name, "카테고리")
        
        object.__setattr__(self, "name", normalized_name)
    
    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name
        }
        
    @classmethod
    def from_dict(cls, data: dict[str, str]) -> "Category":
        try:
            name = data["name"]
        except KeyError as error:
            raise ValueError("카테고리 데이터에 필수 필드가 없습니다: name") from error

        return cls(name=name)