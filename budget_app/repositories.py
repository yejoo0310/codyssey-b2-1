import json
import os
import tempfile
from collections.abc import Iterator, Iterable
from pathlib import Path
from typing import Any

from budget_app.errors import DataAccessError, DataFormatError
from budget_app.models import Transaction


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
                f"저장 파일을 준비하지 못했습니다: {self.file_path}",
                hind="저장 경로와 파일 접근 권한을 확인해 주세요."
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
                            f"JSONL 형식이 올바르지 않습니다: {self.file_path}의 {line_number}번째 줄",
                            hint="해당 줄이 올바른 JSON인지 확인해 주세요."
                        ) from error
                    
                    if not isinstance(data, dict):
                        raise DataFormatError(
                            f"JSONL 데이터가 객체 형식이 아닙니다: {self.file_path}의 {line_number}번째 줄",
                            hint="각 줄은 {\"필드\": \"값\"} 형태의 JSON 객체여야 합니다."
                        )
                    
                    yield data
        except OSError as error:
            raise DataAccessError(
                f"저장 파일을 읽지 못했습니다: {self.file_path}",
                hint="파일 경로와 읽기 권한을 확인해 주세요."
            ) from error
            
    """딕셔너리 한 건을 JSONL 파일 끝에 추가"""
    def _append_dict(self, data: dict[str, Any]) -> None:
        try:
            json_line = json.dumps(
                data,
                ensure_ascii=False
            )
        except (TypeError, ValueError) as error:
            raise DataFormatError(
                "JSONL로 저장할 수 없는 데이터가 포함되어 있습니다.",
                hint="저장 데이터는 문자열, 숫자, 불리언, None, 딕셔너리, 리스트로 구성해야 합니다."
            ) from error
        
        try:
            with self.file_path.open(
                "a",
                encoding="utf-8"
            ) as file:
                file.write(json_line + "\n")
        except OSError as error:
            raise DataAccessError(
                f"저장 파일에 데이터를 기록하지 못했습니다: {self.file_path}",
                hint="저장 경로와 파일 쓰기 권한을 확인해 주세요."
            ) from error
            
    """딕셔너리 여러 건을 임시 파일에 기록한 뒤 원본 파일 교체"""
    def _rewrite_dicts(
        self,
        records: Iterable[dict[str, Any]]
    ) -> None:
        temp_path: Path | None = None
        
        try: 
            with tempfile.NamedTemporaryFile(
                mode="w",
                encoding="utf-8",
                dir=self.file_path.parent,
                prefix=f".{self.file_path.name}.",
                suffix=".tmp",
                delete=False
            ) as temp_file:
                temp_path = Path(temp_file.name)
                
                for data in records:
                    try:
                        json_line = json.dumps(
                            data,
                            ensure_ascii=False
                        )
                    except (TypeError, ValueError) as error:
                        raise DataFormatError(
                            "JSONL로 저장할 수 없는 데이터가 포함되어 있습니다.",
                            hint="저장 데이터는 문자열, 숫자, 불리언, None, 딕셔너리, 리스트로 구성해야 합니다."
                        ) from error
                        
                    temp_file.write(json_line + "\n")

                temp_file.flush()
                os.fsync(temp_file.fileno())

            os.replace(temp_path, self.file_path)
    
        except OSError as error:
            raise DataAccessError(
                f"저장 파일을 다시 작성하지 못했습니다: {self.file_path}",
                hint="저장 경로, 파일 쓰기 권한과 디스크 공간을 확인해 주세요."
            ) from error
        
        finally:
            if temp_path is None:
                try:
                    temp_path.unlink(missing_ok=True)
                except OSError:
                    pass
                

"""거래 데이터를 JSONL 파일에 저장하고 조회하는 저장소"""
class TransactionRepository(JsonlRepository):
    """거래 한 건 저장"""
    def add(self, transaction: Transaction) -> None:
        self._append_dict(transaction.to_dict())
        
    """저장된 거래를 파일 순서대로 한 건씩 반환"""
    def iter_all(self) -> Iterable[Transaction]:
        for data in self._iter_dicts():
            yield Transaction.from_dict(data)