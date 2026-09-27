import argparse

from budget_app.dependencies import Services
from budget_app.models import Transaction
from budget_app.validators import (
    normalize_category_name,
    parse_date,
    parse_positive_int,
    parse_tags,
    parse_transaction_type,
    validate_date_range,
)


def print_transaction(transaction: Transaction) -> None:
    print(
        f"{transaction.id} | "
        f"{transaction.date.isoformat()} | "
        f"{transaction.type} | "
        f"{transaction.category} | "
        f"{transaction.amount} | "
        f"{transaction.memo}"
    )


def handle_list(
    args: argparse.Namespace,
    services: Services,
) -> None:
    transactions = services.transaction.list_transaction(
        limit=args.limit
    )

    for transaction in transactions:
        print_transaction(transaction)


def handle_add(
    args: argparse.Namespace,
    services: Services,
) -> None:
    date = parse_date(
        input("날짜(YYYY-MM-DD): "),
        "거래 날짜",
    )

    transaction_type = parse_transaction_type(
        input("타입(income/expense): "),
        "거래 유형",
    )

    category = input("카테고리: ")

    amount = parse_positive_int(
        input("금액(양수): "),
        "거래 금액",
    )

    memo = input("메모(선택): ")

    tags = parse_tags(
        input("태그(쉼표로 구분, 없으면 엔터): ")
    )

    transaction = services.transaction.add_transaction(
        transaction_type=transaction_type,
        date=date,
        amount=amount,
        category=category,
        memo=memo,
        tags=tags,
    )

    print(f"[저장 완료] id={transaction.id}")


def handle_category_add(
    args: argparse.Namespace,
    services: Services,
) -> None:
    name = input("카테고리명: ")

    category = services.category.add_category(name)

    print(f"[저장 완료] category={category.name}")


def handle_category_list(
    args: argparse.Namespace,
    services: Services,
) -> None:
    found = False

    for category in services.category.list_category():
        print(f"- {category.name}")
        found = True

    if not found:
        print("등록된 카테고리가 없습니다.")


def handle_category_remove(
    args: argparse.Namespace,
    services: Services,
) -> None:
    name = input("삭제할 카테고리명: ")

    normalized_name = normalize_category_name(name)

    services.category.remove_category(normalized_name)

    print(f"[삭제 완료] category={normalized_name}")


def handle_delete(
    args: argparse.Namespace,
    services: Services,
) -> None:
    services.transaction.delete_transaction(
        args.transaction_id
    )

    print(f"[삭제 완료] id={args.transaction_id}")


def handle_update(
    args: argparse.Namespace,
    services: Services,
) -> None:
    if all(
        value is None
        for value in (
            args.date,
            args.transaction_type,
            args.category,
            args.amount,
            args.memo,
            args.tags,
        )
    ):
        raise ValueError(
            "수정할 항목을 하나 이상 지정해야 합니다."
        )

    date = (
        parse_date(
            args.date,
            "거래 날짜",
        )
        if args.date is not None
        else None
    )

    transaction_type = (
        parse_transaction_type(
            args.transaction_type,
            "거래 유형",
        )
        if args.transaction_type is not None
        else None
    )

    amount = (
        parse_positive_int(
            args.amount,
            "거래 금액",
        )
        if args.amount is not None
        else None
    )

    tags = (
        parse_tags(args.tags)
        if args.tags is not None
        else None
    )

    transaction = services.transaction.update_transaction(
        args.transaction_id,
        transaction_type=transaction_type,
        date=date,
        amount=amount,
        category=args.category,
        memo=args.memo,
        tags=tags,
    )

    print(f"[수정 완료] id={transaction.id}")


def handle_search(
    args: argparse.Namespace,
    services: Services,
) -> None:
    date_from = (
        parse_date(
            args.date_from,
            "조회 시작일",
        )
        if args.date_from is not None
        else None
    )

    date_to = (
        parse_date(
            args.date_to,
            "조회 종료일",
        )
        if args.date_to is not None
        else None
    )

    validate_date_range(
        date_from,
        date_to,
    )

    transaction_type = (
        parse_transaction_type(
            args.transaction_type,
            "거래 유형",
        )
        if args.transaction_type is not None
        else None
    )

    for transaction in services.transaction.search_transaction(
        date_from=date_from,
        date_to=date_to,
        category=args.category,
        transaction_type=transaction_type,
        query=args.query,
        tag=args.tag,
    ):
        print_transaction(transaction)


def handle_budget_set(
    args: argparse.Namespace,
    services: Services,
) -> None:
    amount = parse_positive_int(
        args.amount,
        "예산 금액",
    )

    budget = services.budget.set_budget(
        month=args.month,
        amount=amount,
    )

    print(
        f"[저장 완료] "
        f"{budget.month} 예산 {budget.amount}원"
    )


def handle_summary(
    args: argparse.Namespace,
    services: Services,
) -> None:
    summary = services.summary.get_monthly_summary(
        args.month
    )

    top_categories = (
        services.summary.get_top_expense_categories(
            args.month,
            top=args.top,
        )
    )

    if summary.transaction_count == 0:
        print("데이터 없음")
        return

    print(f"총 수입: {summary.total_income}원")
    print(f"총 지출: {summary.total_expense}원")
    print(f"잔액: {summary.balance}원")

    if summary.budget is not None:
        print(
            f"예산: {summary.budget}원 "
            f"(사용률 {summary.budget_usage_rate:.1f}%)"
        )

        if summary.budget_exceeded:
            print("[경고] 예산을 초과했습니다.")

    print()
    print(f"지출 TOP {args.top}")

    for rank, (category, amount) in enumerate(
        top_categories,
        start=1,
    ):
        print(
            f"{rank}) "
            f"{category} "
            f"{amount}원"
        )


def handle_import(
    args: argparse.Namespace,
    services: Services,
) -> None:
    result = services.import_export.import_csv(
        args.source_path
    )

    print(
        f"[완료] imported={result.imported}, "
        f"skipped={result.skipped}"
    )


def handle_export(
    args: argparse.Namespace,
    services: Services,
) -> None:
    date_from = (
        parse_date(
            args.date_from,
            "내보내기 시작일",
        )
        if args.date_from is not None
        else None
    )

    date_to = (
        parse_date(
            args.date_to,
            "내보내기 종료일",
        )
        if args.date_to is not None
        else None
    )

    exported = services.import_export.export_csv(
        args.output_path,
        month=args.month,
        date_from=date_from,
        date_to=date_to,
    )

    print(
        f"[완료] {args.output_path} "
        f"({exported} records)"
    )