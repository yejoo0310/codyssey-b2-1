from pathlib import Path

from budget_app.errors import DataAccessError


"""JSONL 저장 파일의 공통 처리를 담당"""
class JsonlRepository:
    def __init__(self, file_path: Path) -> None:
        self.file_path = file_path
        self._ensure_file()
    
    def _ensure_file(self) -> None:
        try:
            self.file_path.parent.mkdir(
                parents=True,
                exist_ok=True
            )
            self.file_path.touch(exist_ok=True)
        except OSError as error:
            raise DataAccessError(
                f"[오류] 저장 파일을 준비하지 못했습니다: {self.file_path}",
                hind="[힌트] 저장 경로와 파일 접근 권한을 확인해 주세요."
            ) from error