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
            
        