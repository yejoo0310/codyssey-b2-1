class BudgetAppError(Exception):
    """budget app 프로그램에서 예상 가능한 오류의 최상위 예외"""
    def __init__(
        self,
        message: str,
        *,
        hint: str | None = None
    ) -> None:
        super().__init__(message)
        self.message = message
        self.hint = hint
        

class DataAccessError(BudgetAppError):
    """저장 파일이나 디렉터리를 읽고 쓰지 못한 상황"""


class DataFormatError(BudgetAppError):
    """JSONL 또는 CSV 데이터 형식이 올바르지 않은 경우"""


class NotFoundError(BudgetAppError):
    """요청한 거래, 카테고리 또는 예산을 찾지 못한 경우"""


class DuplicateError(BudgetAppError):
    """이미 존재하는 데이터를 다시 추가하려는 경우"""


class CategoryInUseError(BudgetAppError):
    """거래에서 사용 중인 카테고리를 삭제하려는 경우"""
    
class ValidationError(BudgetAppError):
    """사용자 입력이나 명령 옵션이 유효하지 않은 경우"""