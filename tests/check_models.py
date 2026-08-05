from datetime import date

from budget_app.models import Budget, Category, Transaction


def check_transaction() -> None:
    print("=== Transaction 직접 생성 ===")

    transaction = Transaction(
        id="  TX-001  ",
        type="expense",
        date=date(2026, 8, 4),
        amount=15000,
        category="  food  ",
        memo="  점심 식사  ",
        tags=[" meal ", "lunch", "meal", ""],
    )

    print(transaction)
    print(transaction.to_dict())

    print("\n=== Transaction 딕셔너리 복원 ===")

    restored = Transaction.from_dict({
        "id": "TX-002",
        "type": "income",
        "date": "2026-08-01",
        "amount": "3000000",
        "category": "salary",
        "memo": "월급",
        "tags": ["monthly", "income"],
    })

    print(restored)
    print(restored.to_dict())


def check_budget() -> None:
    print("\n=== Budget 점검 ===")

    budget = Budget(
        month=" 2026-08 ",
        amount=500000,
    )

    print(budget)
    print(budget.to_dict())

    restored = Budget.from_dict({
        "month": "2026-09",
        "amount": "600000",
    })

    print(restored)
    print(restored.to_dict())


def check_category() -> None:
    print("\n=== Category 점검 ===")

    category = Category("  food  ")

    print(category)
    print(category.to_dict())

    restored = Category.from_dict({
        "name": "transport",
    })

    print(restored)
    print(restored.to_dict())


def check_invalid_data() -> None:
    print("\n=== 잘못된 데이터 점검 ===")

    invalid_cases = [
        lambda: Category("   "),
        lambda: Budget("2026-13", 100000),
        lambda: Budget("2026-08", 0),
        lambda: Transaction(
            id="TX-003",
            type="expense",
            date=date(2026, 8, 4),
            amount=-1000,
            category="food",
        ),
        lambda: Transaction.from_dict({
            "id": "TX-004",
            "type": "expense",
            "date": "2026-08-04",
            "amount": 10000,
            "category": "food",
            "unknown": "허용되지 않는 필드",
        }),
    ]

    for index, create_model in enumerate(invalid_cases, start=1):
        try:
            create_model()
        except (TypeError, ValueError) as error:
            print(f"{index}. 예상한 오류 발생: {error}")
        else:
            print(f"{index}. 문제: 오류가 발생하지 않았습니다.")


def main() -> None:
    check_transaction()
    check_budget()
    check_category()
    check_invalid_data()


if __name__ == "__main__":
    main()