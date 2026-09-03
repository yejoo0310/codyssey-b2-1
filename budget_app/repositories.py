import json
import os
import tempfile
from collections.abc import Iterator, Iterable
from pathlib import Path
from typing import Any
from datetime import date as Date

from budget_app.errors import (
    DataAccessError, 
    DataFormatError, 
    DuplicateError,
    NotFoundError
)
from budget_app.models import Budget, Category, Transaction
from budget_app.validators import normalize_category_name


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
                hint="저장 경로와 파일 접근 권한을 확인해 주세요."
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
            if temp_path is not None:
                try:
                    temp_path.unlink(missing_ok=True)
                except OSError:
                    pass
                

"""거래 데이터를 JSONL 파일에 저장하고 조회하는 저장소"""
class TransactionRepository(JsonlRepository):
    @staticmethod
    def _sort_key(transaction: Transaction) -> tuple[Date, str]:
        return (transaction.date, transaction.id)
    
    """거래 한 건 저장"""
    def add(self, transaction: Transaction) -> None:
        if (self.exists(transaction.id)):
            raise DuplicateError(
                f"이미 존재하는 ID입니다: {transaction.id}",
                hint="새로운 거래 ID를 생성한 뒤 다시 시도해 주세요."
            )
        
        def sorted_records() -> Iterator[dict[str, Any]]:
            inserted = False
            
            for saved_transaction in self.iter_all():
                if not inserted and self._sort_key(transaction) > self._sort_key(saved_transaction):
                    yield transaction.to_dict()
                    inserted = True
                    
                yield saved_transaction.to_dict()
            
            if not inserted:
                yield transaction.to_dict()
                
        self._rewrite_dicts(sorted_records())
        
    """저장된 거래를 파일 순서대로 한 건씩 반환"""
    def iter_all(self) -> Iterator[Transaction]:
        for data in self._iter_dicts():
            try:
                yield Transaction.from_dict(data)
            except (TypeError, ValueError) as error:
                raise DataFormatError(
                    f"거래 데이터 형식이 올바르지 않습니다: {self.file_path}",
                    hint="거래의 필드값을 확인해 주세요."
                ) from error
            
    """ID가 일치하는 거래를 찾고, 없으면 None 반환"""        
    def _find_by_id(self, transaction_id: str) -> Transaction | None:
        for transaction in self.iter_all():
            if transaction.id == transaction_id:
                return transaction
        return None
            
    """ID가 일치하는 거래 반환"""
    def get_by_id(self, transaction_id: str) -> Transaction:
        transaction = self._find_by_id(transaction_id)
        
        if transaction is None:
            raise NotFoundError(
                f"거래를 찾을 수 없습니다: {transaction_id}",
                hint="거래 ID를 확인한 뒤 다시 시도해 주세요."
            )
        return transaction
            
        
    """주어진 ID의 거래가 존재하는지 확인"""
    def exists(self, transaction_id: str) -> bool:
        return self._find_by_id(transaction_id) is not None
    
    """기존 거래를 전달받은 객체로 교체"""
    def update(self, transaction: Transaction) -> None:
        if not self.exists(transaction.id):
            raise NotFoundError(
                f"거래를 찾을 수 없습니다: {transaction.id}",
                hint="거래 ID를 확인한 뒤 다시 시도해 주세요."
            )
    
        def sorted_records() -> Iterator[dict[str, Any]]:
            inserted = False

            for saved_transaction in self.iter_all():
                if saved_transaction.id == transaction.id:
                    continue

                if (
                    not inserted
                    and self._sort_key(transaction)
                    > self._sort_key(saved_transaction)
                ):
                    yield transaction.to_dict()
                    inserted = True

                yield saved_transaction.to_dict()

            if not inserted:
                yield transaction.to_dict()

        self._rewrite_dicts(
            sorted_records()
        )
        
    """ID가 일치하는 거래 삭제"""
    def delete(self, transaction_id: str) -> None:
        if not self.exists(transaction_id):
            raise NotFoundError(
                f"거래를 찾을 수 없습니다: {transaction_id}",
                hint="거래 ID를 확인한 뒤 다시 시도해 주세요."
            )
        
        def remaining_records() -> Iterator[dict[str, Any]]:
            for saved_transaction in self.iter_all():
                if saved_transaction.id != transaction_id:
                    yield saved_transaction.to_dict()
        
        self._rewrite_dicts(remaining_records())
    
    def generate_id(self) -> str:
        max_number = 0
        
        for transaction in self.iter_all():
            number = self._parse_id_number(transaction.id)
            
            if number is not None:
                max_number = max(number, max_number)
        
        return f"TX-{max_number + 1:06d}"

    @staticmethod
    def _parse_id_number(transaction_id: str) -> int | None:
        if not transaction_id.startswith("TX-"):
            return None
        
        try:
            return int(transaction_id[3:])
        except ValueError:
            return None
        
        
"""카테고리 데이터를 JSONL 파일에 저장하고 조회하는 저장소"""
class CategoryRepository(JsonlRepository):
    def iter_all(self) -> Iterator[Category]:
        for data in self._iter_dicts():
            try:
                yield Category.from_dict(data)
            except (TypeError, ValueError) as error:
                raise DataFormatError(
                    f"카테고리 데이터 형식이 올바르지 않습니다: {self.file_path}",
                    hint="카테고리 데이터의 name 필드를 확인해 주세요."
                ) from error
            
    def _find_by_name(self, name: str) -> Category | None:
        normalized_name = normalize_category_name(name)
        
        for category in self.iter_all():
            if category.name == normalized_name:
                return category
        return None

    def get_by_name(self, name: str) -> Category:
        category = self._find_by_name(name)
        
        if category is None:
            raise NotFoundError(
                f"카테고리를 찾을 수 없습니다: {name}",
                hint="등록된 카테고리 이름을 확인해 주세요."
            )
        return category

    def exists(self, name: str) -> bool:
        return self._find_by_name(name) is not None
    
    def add(self, category: Category) -> None:
        if self.exists(category.name):
            raise DuplicateError(
                f"이미 존재하는 카테고리입니다: {category.name}",
                hint="다른 카테고리 이름을 입력해 주세요."
            )
        self._append_dict(category.to_dict())
        
    def remove(self, name: str) -> None:
        normalized_name = normalize_category_name(name)
        if not self.exists(normalized_name):
            raise NotFoundError(
                f"삭제할 카테고리를 찾을 수 없습니다: {normalized_name}",
                hint="등록된 카테고리 이름을 확인해 주세요."
            )
        
        def remaining_records() -> Iterator[dict[str, str]]:
            for category in self.iter_all():
                if category.name != normalized_name:
                    yield category.to_dict()

        self._rewrite_dicts(remaining_records())
        

"""월별 예산 데이터를 JSONL 파일에 저장하고 조회하는 저장소"""
class BudgetRepository(JsonlRepository):
    def iter_all(self) -> Iterator[Budget]:
        for data in self._iter_dicts():
            try:
                yield Budget.from_dict(data)
            except (TypeError, ValueError) as error:
                raise DataFormatError(
                    f"예산 데이터 형식이 올바르지 않습니다: {self.file_path}",
                    hint="예산의 month와 amount 값을 확인해 주세요."
                ) from error
        
    def _find_by_month(self, month: str) -> Budget | None:
        normalized_month = month.strip()
        
        for budget in self.iter_all():
            if budget.month == normalized_month:
                return budget
        return None
    
    def get_by_month(self, month: str) -> Budget | None:
        return self._find_by_month(month)
    
    def exists(self, month: str) -> bool:
        return self._find_by_month(month) is not None
    
    def set(self, budget: Budget) -> None:
        if not self.exists(budget.month):
            self._append_dict(budget.to_dict())
            return
        
        def replacement_records() -> Iterator[dict[str, int]]:
            for saved_budget in self.iter_all():
                if saved_budget.month == budget.month:
                    yield budget.to_dict()
                else:
                    yield saved_budget.to_dict()
                    
        self._rewrite_dicts(replacement_records())