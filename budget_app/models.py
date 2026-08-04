import re

from dataclasses import dataclass, field
from datetime import date as Date
from typing import Any, Literal

TransactionType = Literal["income", "expense"]


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

    """객체 생성 후 필드 값을 정리하고 검증"""
    def __post_init__(self) -> None:
        self.id = self.id.strip()
        self.category = self.category.strip()
        self.memo = self.memo.strip()
        self.tags = self._normalize_tags(self.tags)

        if not self.id:
            raise ValueError("거래 ID는 비어 있을 수 없습니다.")

        if self.type not in ("income", "expense"):
            raise ValueError("거래 유형은  income 또는 expense여야 합니다.")

        if not isinstance(self.date, Date):
            raise ValueError("거래 날짜는 datetime.date 객체여야 합니다.")

        if self.amount <= 0:
            raise ValueError("거래 금액은 0보다 커야 합니다.")

        if not self.category:
            raise ValueError("카테고리는 비어 있을 수 없습니다.")


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


    """JSONL에서 읽은 딕셔너리를 Transaction으로 변환"""
    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Transaction":
        try:
            transaction_id = str(data["id"])
            transaction_type = cls._parse_type(data["type"])
            transaction_date = cls._parse_date(data["date"])
            amount = cls._parse_amount(data["amount"])
            category = str(data["category"])
        except KeyError as error:
            missing_field = error.args[0]
            raise ValueError(f"거래 데이터에 필수 필드가 없습니다: {missing_field}") from error

        return cls(
            id=transaction_id,
            type=transaction_type,
            date=transaction_date,
            amount=amount,
            category=category,
            memo=str(data.get("memo", "")),
            tags=cls._parse_tags(data.get("tags", []))
        )


    @staticmethod
    def _parse_type(value: object) -> TransactionType:
        if value == "income":
            return "income"

        if value == "expense":
            return "expense"

        raise ValueError("거래 유형은 income 또는 expense여야 합니다.")

    @staticmethod
    def _parse_date(value: object) -> Date:
        if isinstance(value, Date):
            return value

        if not isinstance(value, str):
            raise ValueError("거래 날짜는 YYYY-MM-DD 형식의 문자열이여야 합니다.")

        try:
            return Date.fromisoformat(value)
        except ValueError as error:
            raise ValueError("거래 날짜 형식이 올바르지 않습니다. YYYY-MM-DD 형식으로 입력해 주세요.") from error


    @staticmethod
    def _parse_amount(value: object) -> int:
        if isinstance(value, bool):
            raise ValueError("거래 금액은 양수 정수여야 합니다.")

        if isinstance(value, int):
            amount = value
        elif isinstance(value, str):
            stripped_value = value.strip()
            if not stripped_value.isdigit():
                raise ValueError("거래 금액은 양수 정수여야 합니다.")
            amount = int(stripped_value)
        else:
            raise ValueError("거래 금액은 양수 정수여야 합니다.")

        if amount <= 0:
            raise ValueError("거래 금액은 0보다 커야 합니다.")

        return amount

    @staticmethod
    def _parse_tags(value: object) -> list[str]:
        if value is None:
            return []

        if isinstance(value, str):
            return [
                tag.strip()
                for tag in value.split(",")
                if tag.strip()
            ]

        if isinstance(value, list):
            return [
                str(tag).strip()
                for tag in value
                if str(tag).strip()
            ]

        raise ValueError("태그는 문자열 또는 문자열 목록이어야 합니다.")

    @staticmethod
    def _normalize_tags(tags: list[str]) -> list[str]:
        normalized_tags: list[str] = []

        for tag in tags:
            normalized_tag = str(tag).strip()
            if normalized_tag and normalized_tag not in normalized_tags:
                normalized_tags.append(normalized_tag)

        return normalized_tags
    
    
"""특정 월에 설정된 예산을 나타내는 데이터 모델"""
@dataclass
class Budget(slots=True):
    month: str
    amount: int
    
    def __post_init__(self) -> None:
        if not isinstance(self.month, str):
            raise ValueError("예산 월은 YYYY-MM 형식의 문자열이어야 합니다.")

        self.month = self.month.strip()
        self._validate_month(self.month)
        self._validate_amount(self.amount)

    def to_dict(self) -> dict[str, Any]:
        return {
            "month": self.month,
            "amount": self.amount
        }
        
    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Budget":
        try:
            month = cls._parse_month(data["month"])
            amount = cls._parse_amount(data["amount"])
        except KeyError as error:
            missing_field = error.logs[0]

            raise ValueError(f"예산 데이터에 필수 필드가 없습니다 : {missing_field}") from error
        
        return cls(
            month = month,
            amount = amount
        )
        
    @staticmethod
    def _parse_month(value: object) -> str:
        if not isinstance(value, str):
            raise ValueError("예산 월은 YYYY-MM 형식의 문자열이어야 합니다.")
        month = value.strip()
        Budget._validate_month(month)
        
        return month
    
    @staticmethod
    def _validate_month(month: str) -> None:
        if re.fullmatch(r"\d{4}-(0[1-9]|1[0-2])", month) is None:
            raise ValueError("예산 월 형식이 올바르지 않습니다. YYYY-MM 형식으로 입력해 주세요.")
        
        try:
            Date.isoformat(f"{month}-01")
        except ValueError as error:
            raise ValueError("예산 월 형식이 올바르지 않습니다. YYYY-MM 형식으로 입력해 주세요.") from error
    
    @staticmethod
    def _validate_amount(amount: int) -> None:
        if isinstance(amount, bool) or not isinstance(amount, int):
            raise ValueError("예산 금액은 양수 정수여야 합니다.")
        
        if amount <= 0:
            raise ValueError("예산 금액은 0보다 커야 합니다.")