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

    """모든 생성 경로에서 객체의 최종 상태를 검증"""
    def __post_init__(self) -> None:
        self.id = self._normalize_required_text(
            self.id,
            "거래 ID"
        )
        self.category = self._normalize_required_text(
            self.category,
            "카테고리"
        )
        self.memo = self._normalize_optional_text(self.memo)
        
        self._validate_type(self.type)
        self._validate_date(self.date)
        self._validate_amount(self.amount)

        self.tags = self._normalize_tags(self.tags)


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
                id=cls._parse_required_text(
                    data["id"],
                    "거래 ID"
                ),
                type=cls._parse_type(data["type"]),
                date=cls._parse_date(data["date"]),
                amount=cls._parse_amount(data["amount"]),
                category=cls._parse_required_text(
                    data["category"],
                    "카테고리"
                ),
                memo=cls._parse_optional_text(data.get("memo", "")),
                tags=cls._parse_tags(data.get("tags", []))
            )
        except KeyError as error:
            missing_field = error.args[0];
            raise ValueError(f"거래 데이터에 필수 필드가 없습니다: {missing_field}") from error

    @staticmethod
    def _validate_type(value: object) -> None:
        if value not in ("income", "expense"):
            raise ValueError("거래 유형은 income 또는 expense여야 합니다.")
    
    @staticmethod
    def _validate_date(value: object) -> None:
        if not isinstance(value, Date):
            raise ValueError("거래 날짜는 datetime.date 객체여야 합니다.")
    
    @staticmethod
    def _validate_amount(value: object) -> None:
        if isinstance(value, bool) or not isinstance(value, int):
            raise ValueError("거래 금액은 양수 정수여야 합니다.")
        
        if value <= 0:
            raise ValueError("거래 금액은 0보다 커야 합니다.")
    
    @staticmethod
    def _parse_type(value: object) -> TransactionType:
        Transaction._validate_type(value)
        
        if value == "income":
            return "income"
        if value == "expense":
            return "expense"
    
    @staticmethod
    def _parse_date(value: object) -> Date:
        if isinstance(value, Date):
            return value

        if not isinstance(value, str):
            raise ValueError("거래 날짜는 YYYY-MM-DD 형식의 문자열이어야 합니다.")
        
        try:
            return Date.fromisoformat(value.strip())
        except ValueError as error:
            raise ValueError("거래 날짜 형식이 올바르지 않습니다. YYYY-MM-DD 형식으로 입력해 주세요.") from error
    
    @staticmethod
    def _parse_amount(value: object) -> int:
        if isinstance(value, bool):
            raise ValueError("거래 금액은 정수 양수여야 합니다.")

        if isinstance(value, int):
            amount = value
        elif isinstance(value, str):
            normalized = value.strip()
            if not normalized.isdigit():
                raise ValueError("거래 금액은 정수 양수여야 합니다.")
            amount = int(normalized)
        else:
            raise ValueError("거래 금액은 정수 양수여야 합니다.")
        
        Transaction._validate_amount(amount)
        return amount

    @staticmethod
    def _parse_required_text(
        value: object,
        field_name: str
    ) -> str:
        if not isinstance(value, str):
            raise ValueError(f"{field_name}는 문자열이어야 합니다.")
        
        normalized = value.strip()
        
        if not normalized:
            raise ValueError(f"{field_name}는 비어 있을 수 없습니다.")
        
        return normalized
    
    @staticmethod
    def _parse_optional_text(value: object) -> str:
        if value is None:
            return ""
        
        if not isinstance(value, str):
            raise ValueError("메모는 문자열이어야 합니다.")

        return value.strip()
    
    @staticmethod
    def _parse_tags(value: object) -> list[str]:
        if value is None:
            return []
        
        if isinstance(value, str):
            raw_tags = value.split(",")
        elif isinstance(value, list):
            if not all(isinstance(tag, str) for tag in value):
                raise ValueError("모든 태그는 문자열이어야 합니다.")
            raw_tags = value
        else:
            raise ValueError("태그는 문자열 또는 문자열 목록이어야 합니다.")
        
        return [
            tag.strip()
            for tag in raw_tags
            if tag.strip()
        ]
        
    @staticmethod
    def _normalize_required_text(
        value: object,
        field_name: str
    ) -> str:
        return Transaction._parse_required_text(value, field_name)
    
    @staticmethod
    def _normalize_optional_text(value: object) -> str:
        return Transaction._parse_optional_text(value)

    @staticmethod
    def _normalize_tags(value: object) -> list[str]:
        if not isinstance(value, list):
            raise ValueError("태그는 문자열 목록이어야 합니다.")
        
        if not all(isinstance(tag, str) for tag in value):
            raise ValueError("모든 태그는 문자열이어야 합니다.")
        
        normalized_tags: list[str] = []
        
        for tag in value:
            normalized_tag = tag.strip()
            if (normalized_tag and normalized_tag not in normalized_tags):
                normalized_tags.append(normalized_tag)
        
        return normalized_tags
    
    
"""특정 월에 설정된 예산을 나타내는 데이터 모델"""
@dataclass(slots=True)
class Budget:
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
            return cls(
                month = cls._parse_month(data["month"]),
                amount = cls._parse_amount(data["amount"])
            )
        except KeyError as error:
            missing_field = error.args[0]

            raise ValueError(f"예산 데이터에 필수 필드가 없습니다 : {missing_field}") from error
        
    @staticmethod
    def _validate_month(value: str) -> None:
        if not isinstance(value, str):
            raise ValueError("예산 월은 YYYY-MM 형식의 문자열이어야 합니다.")

        if re.fullmatch(r"\d{4}-(0[1-9]|1[0-2])", value) is None:
            raise ValueError("예산 월 형식이 올바르지 않습니다. YYYY-MM 형식으로 입력해 주세요.")
    
    @staticmethod
    def _validate_amount(value: int) -> None:
        if isinstance(value, bool) or not isinstance(value, int):
            raise ValueError("예산 금액은 양수 정수여야 합니다.")
        
        if value <= 0:
            raise ValueError("예산 금액은 0보다 커야 합니다.")

    @staticmethod
    def _parse_month(value: object) -> str:
        if not isinstance(value, str):
            raise ValueError("예산 월은 YYYY-MM 형식의 문자열이어야 합니다.")
        month = value.strip()
        Budget._validate_month(month)
        
        return month
    
    @staticmethod
    def _parse_amount(value: object) -> int:
        if isinstance(value, bool):
            raise ValueError("거래 금액은 정수 양수여야 합니다.")
        
        if isinstance(value, int):
            amount = value
        elif isinstance(value, str):
            normalized = value.strip()
            if not normalized.isdigit():
                raise ValueError("거래 금액은 정수 양수여야 합니다.")
            amount = int(normalized)
        else:
            raise ValueError("거래 금액은 정수 양수여야 합니다.")
        
        Budget._validate_amount(amount)
        return amount
    
    
"""거래에 사용할 카테고리를 나타내는 데이터 모델"""
@dataclass(slots=True, frozen=True)
class Category:
    name: str
    
    def __post_init__(self) -> None:
        if not isinstance(self.name, str):
            raise ValueError("카테고리 이름은 문자열이어야 합니다.")
        
        normalized_name = self.name.strip()
        
        if not normalized_name:
            raise ValueError("카테고리 이름은 비어 있을 수 없습니다.")
        
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