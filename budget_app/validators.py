from datetime import date as Date
from datetime import datetime as Datetime

from budget_app.types import TransactionType


def normalize_required_text(value: object, field_name: str) -> str:
    if not isinstance(value, str):
        raise ValueError(f"{field_name}: 문자열이어야 합니다.")

    normalized = value.strip()
    
    if not normalized:
        raise ValueError(f"{field_name}: 비어있을 수 없습니다.")

    return normalized

def normalize_optional_text(value: object, field_name: str) -> str:
    if value is None:
        return ""
    
    if not isinstance(value, str):
        raise ValueError(f"{field_name}: 문자열이어야 합니다.")
    
    return value.strip()

def validate_positive_int(value: object, field_name: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValueError(f"{field_name}: 정수 양수여야 합니다.")
    
    if value <= 0:
        raise ValueError(f"{field_name}: 0보다 커야 합니다.")
    
    return value

def parse_positive_int(value: object, field_name: str) -> int:
    if isinstance(value, bool):
        raise ValueError(f"{field_name}: 정수 양수여야 합니다.")
    
    if isinstance(value, int):
        parsed = value
    elif isinstance(value, str):
        normalized = value.strip()
        
        if not normalized.isdigit():
            raise ValueError(f"{field_name}: 정수 양수여야 합니다.")

        parsed = int(normalized)
    else:
        raise ValueError(f"{field_name}: 정수 양수여야 합니다.")
        
    return validate_positive_int(
        parsed,
        field_name
    )
            
def validate_date(value: object, field_name: str) -> Date:
    if isinstance(value, Datetime) or not isinstance(value, Date):
        raise ValueError(f"{field_name}: datetime.date 객체여야 합니다.")
    return value

def parse_date(value: object, field_name: str) -> Date:
    if isinstance(value, Date):
        return validate_date(
            value,
            field_name
        )
    
    if not isinstance(value, str):
        raise ValueError(f"{field_name}: YYYY-MM-DD 형식의 문자열이어야 합니다.")
    
    normalized = value.strip()

    try:
        parsed = Date.fromisoformat(normalized)
    except ValueError as error:
        raise ValueError(f"{field_name}: YYYY-MM-DD 형식의 올바른 날짜여야 합니다.") from error
    
    return validate_date(
        parsed,
        field_name
    )
    
def validate_transaction_type(value: object, field_name: str) -> TransactionType:
    if value == "income":
        return "income"
    
    if value == "expense":
        return "expense"

    raise ValueError(f"{field_name}: income 또는 expense여야 합니다.")

def parse_transaction_type(value: object, field_name: str) -> TransactionType:
    if not isinstance(value, str):
        raise ValueError(f"{field_name}: 문자열이어야 합니다.")
    
    normalized = value.strip().lower()
    
    return validate_transaction_type(
        normalized,
        field_name
    )