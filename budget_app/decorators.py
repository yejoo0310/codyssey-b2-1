import sys

from collections.abc import Callable
from functools import wraps

from budget_app.errors import BudgetAppError


def handle_cli_errors(
    func: Callable[[], int],
) -> Callable[[], int]:
    @wraps(func)
    def wrapper() -> int:
        try:
            return func()

        except BudgetAppError as error:
            print(
                f"[오류] {error.message}",
                file=sys.stderr,
            )

            if error.hint:
                print(
                    f"[힌트] {error.hint}",
                    file=sys.stderr,
                )

            return 1

        except ValueError as error:
            print(
                f"[오류] {error}",
                file=sys.stderr,
            )

            print(
                "[힌트] 입력값과 형식을 확인한 뒤 다시 시도해 주세요.",
                file=sys.stderr,
            )

            return 1

        except KeyboardInterrupt:
            print(
                "\n[오류] 사용자에 의해 작업이 중단되었습니다.",
                file=sys.stderr,
            )

            return 130

    return wrapper