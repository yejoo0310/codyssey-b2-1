import argparse
import sys

from pathlib import Path

from budget_app.cli_handlers import (
    handle_add,
    handle_budget_set,
    handle_category_add,
    handle_category_list,
    handle_category_remove,
    handle_delete,
    handle_export,
    handle_import,
    handle_list,
    handle_search,
    handle_summary,
    handle_update,
)


DEFAULT_DATA_DIR = Path("./data")


class BudgetArgumentParser(argparse.ArgumentParser):
    def error(self, message: str) -> None:
        self.print_usage(sys.stderr)

        print(
            f"[오류] {message}",
            file=sys.stderr,
        )

        print(
            "[힌트] --help 옵션으로 사용 방법을 확인해 주세요.",
            file=sys.stderr,
        )

        raise SystemExit(2)


def build_parser() -> argparse.ArgumentParser:
    parser = BudgetArgumentParser(
        prog="budget_app",
        description="파일 기반 콘솔 가계부 프로그램",
    )

    parser.add_argument(
        "--data-dir",
        type=Path,
        default=DEFAULT_DATA_DIR,
        help="데이터 저장 디렉터리 (기본값: ./data)",
    )

    subparsers = parser.add_subparsers(
        dest="command",
        required=True,
        parser_class=BudgetArgumentParser,
    )

    # add
    add_parser = subparsers.add_parser(
        "add",
        help="거래를 추가합니다.",
        description=(
            "대화형 입력으로 날짜, 거래 유형, "
            "카테고리, 금액, 메모와 태그를 입력받아 "
            "새 거래를 저장합니다."
        ),
    )

    add_parser.set_defaults(
        handler=handle_add
    )

    # list
    list_parser = subparsers.add_parser(
        "list",
        help="거래 목록을 조회합니다.",
        description=(
            "저장된 거래를 최신순으로 조회합니다. "
            "--limit 옵션으로 출력할 거래 개수를 "
            "지정할 수 있습니다."
        ),
    )

    list_parser.add_argument(
        "--limit",
        type=int,
        default=20,
        help="조회할 거래 개수 (기본값: 20)",
    )

    list_parser.set_defaults(
        handler=handle_list
    )

    # search
    search_parser = subparsers.add_parser(
        "search",
        help="조건에 맞는 거래를 검색합니다.",
        description=(
            "날짜 범위, 카테고리, 거래 유형, "
            "메모 키워드, 태그 조건을 사용해 "
            "저장된 거래를 검색합니다."
        ),
    )

    search_parser.add_argument(
        "--from",
        dest="date_from",
        help="조회 시작일 (YYYY-MM-DD)",
    )

    search_parser.add_argument(
        "--to",
        dest="date_to",
        help="조회 종료일 (YYYY-MM-DD)",
    )

    search_parser.add_argument(
        "--category",
        help="카테고리",
    )

    search_parser.add_argument(
        "--type",
        dest="transaction_type",
        choices=("income", "expense"),
        help="거래 유형",
    )

    search_parser.add_argument(
        "--q",
        dest="query",
        help="메모 검색어",
    )

    search_parser.add_argument(
        "--tag",
        help="태그",
    )

    search_parser.set_defaults(
        handler=handle_search
    )

    # summary
    summary_parser = subparsers.add_parser(
        "summary",
        help="월별 요약을 조회합니다.",
        description=(
            "지정한 월의 총 수입, 총 지출, 잔액, "
            "예산 사용률과 지출 카테고리 TOP N을 출력합니다."
        ),
    )

    summary_parser.add_argument(
        "--month",
        required=True,
        help="조회할 월 (YYYY-MM)",
    )

    summary_parser.add_argument(
        "--top",
        type=int,
        default=3,
        help="지출 카테고리 TOP N (기본값: 3)",
    )

    summary_parser.set_defaults(
        handler=handle_summary
    )

    # update
    update_parser = subparsers.add_parser(
        "update",
        help="거래를 수정합니다.",
        description=(
            "거래 ID를 기준으로 기존 거래를 수정합니다. "
            "입력한 옵션에 해당하는 필드만 변경되고 "
            "나머지 값은 유지됩니다."
        ),
    )

    update_parser.add_argument(
        "--id",
        required=True,
        dest="transaction_id",
        help="수정할 거래 ID",
    )

    update_parser.add_argument(
        "--date",
        help="변경할 날짜 (YYYY-MM-DD)",
    )

    update_parser.add_argument(
        "--type",
        dest="transaction_type",
        choices=("income", "expense"),
        help="변경할 거래 유형",
    )

    update_parser.add_argument(
        "--category",
        help="변경할 카테고리",
    )

    update_parser.add_argument(
        "--amount",
        type=int,
        help="변경할 금액",
    )

    update_parser.add_argument(
        "--memo",
        help="변경할 메모",
    )

    update_parser.add_argument(
        "--tags",
        help="변경할 태그 (쉼표로 구분)",
    )

    update_parser.set_defaults(
        handler=handle_update
    )

    # delete
    delete_parser = subparsers.add_parser(
        "delete",
        help="거래를 삭제합니다.",
        description=(
            "거래 ID를 기준으로 저장된 "
            "거래 한 건을 삭제합니다."
        ),
    )

    delete_parser.add_argument(
        "--id",
        required=True,
        dest="transaction_id",
        help="삭제할 거래 ID",
    )

    delete_parser.set_defaults(
        handler=handle_delete
    )

    # budget
    budget_parser = subparsers.add_parser(
        "budget",
        help="예산을 관리합니다.",
        description="월별 예산을 설정하고 관리합니다.",
    )

    budget_subparsers = budget_parser.add_subparsers(
        dest="budget_command",
        required=True,
        parser_class=BudgetArgumentParser,
    )

    budget_set_parser = budget_subparsers.add_parser(
        "set",
        help="월 예산을 설정합니다.",
        description=(
            "지정한 월의 예산 금액을 저장합니다. "
            "이미 예산이 설정된 월이면 "
            "기존 금액을 새 금액으로 변경합니다."
        ),
    )

    budget_set_parser.add_argument(
        "--month",
        required=True,
        help="예산 월 (YYYY-MM)",
    )

    budget_set_parser.add_argument(
        "--amount",
        type=int,
        required=True,
        help="예산 금액",
    )

    budget_set_parser.set_defaults(
        handler=handle_budget_set
    )

    # category
    category_parser = subparsers.add_parser(
        "category",
        help="카테고리를 관리합니다.",
        description=(
            "거래에 사용할 카테고리를 "
            "추가하거나 조회하고 삭제합니다."
        ),
    )

    category_subparsers = category_parser.add_subparsers(
        dest="category_command",
        required=True,
        parser_class=BudgetArgumentParser,
    )

    category_add_parser = category_subparsers.add_parser(
        "add",
        help="카테고리를 추가합니다.",
        description=(
            "대화형 입력으로 새 카테고리 이름을 "
            "받아 저장합니다."
        ),
    )

    category_add_parser.set_defaults(
        handler=handle_category_add
    )

    category_list_parser = category_subparsers.add_parser(
        "list",
        help="카테고리 목록을 조회합니다.",
        description=(
            "현재 등록되어 있는 모든 "
            "카테고리를 조회합니다."
        ),
    )

    category_list_parser.set_defaults(
        handler=handle_category_list
    )

    category_remove_parser = category_subparsers.add_parser(
        "remove",
        help="카테고리를 삭제합니다.",
        description=(
            "대화형 입력으로 삭제할 카테고리 이름을 받습니다. "
            "거래에서 사용 중인 카테고리는 삭제할 수 없습니다."
        ),
    )

    category_remove_parser.set_defaults(
        handler=handle_category_remove
    )

    # import
    import_parser = subparsers.add_parser(
        "import",
        help="CSV 파일에서 거래를 가져옵니다.",
        description=(
            "지정한 CSV 파일을 읽어 거래를 일괄 등록합니다. "
            "처리 완료 후 등록된 건수와 건너뛴 건수를 출력합니다."
        ),
    )

    import_parser.add_argument(
        "--from",
        dest="source_path",
        type=Path,
        required=True,
        help="가져올 CSV 파일 경로",
    )

    import_parser.set_defaults(
        handler=handle_import
    )

    # export
    export_parser = subparsers.add_parser(
        "export",
        help="거래를 CSV 파일로 내보냅니다.",
        description=(
            "지정한 월 또는 날짜 범위에 해당하는 거래를 "
            "CSV 파일로 저장합니다. "
            "--month 또는 --from과 --to 조건 중 "
            "하나를 지정해야 합니다."
        ),
    )

    export_parser.add_argument(
        "--out",
        dest="output_path",
        type=Path,
        required=True,
        help="저장할 CSV 파일 경로",
    )

    export_parser.add_argument(
        "--month",
        help="내보낼 월 (YYYY-MM)",
    )

    export_parser.add_argument(
        "--from",
        dest="date_from",
        help="내보내기 시작일 (YYYY-MM-DD)",
    )

    export_parser.add_argument(
        "--to",
        dest="date_to",
        help="내보내기 종료일 (YYYY-MM-DD)",
    )

    export_parser.set_defaults(
        handler=handle_export
    )

    return parser