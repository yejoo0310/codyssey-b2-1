from budget_app.models import Transaction


def normalize_required_text(value: object, field_name: str) -> str:
    if not isinstance(value, str):
        raise ValueError(f"{field_name}: 문자열이어야 합니다.")

    normalized = value.strip()
    
    if not normalized:
        raise ValueError(f"{field_name}: 비어있을 수 없습니다.")

    return normalized