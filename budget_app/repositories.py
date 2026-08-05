import json
from collections.abc import Iterator
from pathlib import Path
from typing import Any

from budget_app.errors import DataAccessError, DataFormatError


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
            
    """JSONL 파일을 한 줄씩 읽어서 딕셔너리로 반환"""
    def _iter_dicts(self) -> Iterator[dict[str, Any]]:
        try:
            with self.file_path.open("r", encoding="utf-8") as file:
                for line_number, raw_line in enumerate(file, start=1):
                    line = raw_line.strip()
                    
                    if not line:
                        continue
                    
                    try:
                        data = json.loads(line)
                    except json.JSONDecodeError as error:
                        raise DataFormatError(
                            f"[오류] JSONL 형식이 올바르지 않습니다: {self.file_path}의 {line_number}번째 줄",
                            hint="[힌트] 해당 줄이 올바른 JSON인지 확인해 주세요."
                        ) from error
                    
                    if not isinstance(data, dict):
                        raise DataFormatError(
                            f"[오류] JSONL 데이터가 객체 형식이 아닙니다: {self.file_path}의 {line_number}번째 줄",
                            hint="[힌트] 각 줄은 {\"필드\": \"값\"} 형태의 JSON 객체여야 합니다."
                        )
                    
                    yield data
        except OSError as error:
            raise DataAccessError(
                f"[오류] 저장 파일을 읽지 못했습니다: {self.file_path}",
                hint="[힌트] 파일 경로와 읽기 권한을 확인해 주세요."
            ) from error