# Codyssey B2-1. 파일 기반 가계부 콘솔 프로그램 만들기

파일 기반으로 데이터를 영구 저장하는 Python 콘솔 가계부 프로그램입니다.

수입과 지출 거래를 추가하고 조회할 수 있으며, 거래 검색, 수정/삭제, 카테고리 관리, 월별 예산 설정, 월별 요약, CSV 가져오기/내보내기 기능을 제공합니다.

데이터는 JSONL 파일에 저장하며, Repository에서는 제너레이터를 사용해 파일을 한 줄씩 읽도록 구성했습니다.

---

## 1. 개발 환경

- Python 3.10 이상
- Python 표준 라이브러리만 사용
- 별도의 외부 패키지 설치 불필요

---

## 2. 실행 방법

프로젝트 루트 디렉터리에서 다음 형식으로 실행합니다.

```bash
python3 -m budget_app <command> [options]
```

전체 명령 도움말:

```bash
python3 -m budget_app --help
```

각 명령의 사용 방법도 `--help`로 확인할 수 있습니다.

```bash
python3 -m budget_app add --help
python3 -m budget_app list --help
python3 -m budget_app search --help
python3 -m budget_app summary --help
```

---

## 3. 데이터 저장 위치

기본 데이터 저장 디렉터리는 다음과 같습니다.

```text
./data
```

프로그램 실행 시 필요한 디렉터리와 파일이 없으면 자동으로 생성됩니다.

기본적으로 다음 3개의 JSONL 파일을 사용합니다.

```text
data/
├── transactions.jsonl
├── categories.jsonl
└── budgets.jsonl
```

각 파일의 역할은 다음과 같습니다.

| 파일 | 내용 |
| --- | --- |
| `transactions.jsonl` | 수입/지출 거래 내역 |
| `categories.jsonl` | 등록된 카테고리 |
| `budgets.jsonl` | 월별 예산 |

JSONL 형식은 한 줄마다 하나의 JSON 객체를 저장합니다.

예:

```json
{"id": "TX-000001", "type": "expense", "date": "2026-09-27", "amount": 15000, "category": "food", "memo": "점심", "tags": ["meal", "lunch"]}
```

### 저장 디렉터리 변경

전역 옵션 `--data-dir`을 사용하면 기본 `./data` 대신 다른 디렉터리를 사용할 수 있습니다.

```bash
python3 -m budget_app --data-dir ./test_data list
```

`--data-dir`은 command 앞에 지정합니다.

---

## 4. 카테고리 관리

거래를 추가하려면 먼저 사용할 카테고리가 등록되어 있어야 합니다.

카테고리 이름은 저장할 때 소문자로 정규화됩니다.

### 카테고리 추가

```bash
python3 -m budget_app category add
```

실행 예:

```text
카테고리명: Food
[저장 완료] category=food
```

### 카테고리 목록

```bash
python3 -m budget_app category list
```

예:

```text
- food
- transport
- salary
```

### 카테고리 삭제

```bash
python3 -m budget_app category remove
```

삭제할 카테고리 이름을 대화형으로 입력합니다.

해당 카테고리가 거래에서 사용 중이면 삭제되지 않습니다.

---

## 5. 거래 추가

`add`는 대화형 입력 방식으로 동작합니다.

```bash
python3 -m budget_app add
```

예:

```text
날짜(YYYY-MM-DD): 2026-09-27
타입(income/expense): expense
카테고리: food
금액(양수): 15000
메모(선택): 점심
태그(쉼표로 구분, 없으면 엔터): meal,lunch
[저장 완료] id=TX-000001
```

거래는 다음 필드를 가집니다.

| 필드 | 설명 |
| --- | --- |
| `id` | 자동 생성되는 고유 거래 ID |
| `type` | `income` 또는 `expense` |
| `date` | `YYYY-MM-DD` 형식의 날짜 |
| `amount` | 0보다 큰 정수 |
| `category` | 등록된 카테고리 |
| `memo` | 선택 입력 |
| `tags` | 선택 입력, 쉼표로 여러 태그 구분 |

태그 입력:

```text
meal,lunch
```

은 내부적으로 다음과 같이 저장됩니다.

```json
["meal", "lunch"]
```

---

## 6. 거래 목록 조회

저장된 거래를 최신순으로 조회합니다.

```bash
python3 -m budget_app list
```

기본 조회 개수는 20개입니다.

```bash
python3 -m budget_app list --limit 5
```

예:

```text
TX-000003 | 2026-09-27 | expense | food | 20000 | 저녁
TX-000002 | 2026-09-25 | expense | transport | 3000 | 버스
TX-000001 | 2026-09-20 | income | salary | 3000000 | 월급
```

`--limit`은 0보다 큰 정수여야 합니다.

---

## 7. 거래 검색

```bash
python3 -m budget_app search [options]
```

사용 가능한 검색 조건:

| 옵션 | 설명 |
| --- | --- |
| `--from` | 조회 시작일 |
| `--to` | 조회 종료일 |
| `--category` | 카테고리 |
| `--type` | `income` 또는 `expense` |
| `--q` | 메모 검색어 |
| `--tag` | 태그 |
 
예:

```bash
python3 -m budget_app search \
    --from 2026-09-01 \
    --to 2026-09-30 \
    --category food \
    --type expense
```

메모 검색:

```bash
python3 -m budget_app search --q 점심
```

메모 검색은 부분 문자열 검색입니다.

태그 검색:

```bash
python3 -m budget_app search --tag meal
```

태그 검색은 저장된 개별 태그와 정확히 일치하는 항목을 검색합니다.

예를 들어 다음 두 태그 입력은 서로 다릅니다.

```text
meal,lunch
```

```text
meal lunch
```

첫 번째는 `meal`, `lunch` 두 개의 태그이고, 두 번째는 `meal lunch`라는 하나의 태그입니다.

공백이 포함된 메모나 태그를 옵션 값으로 전달할 때는 따옴표로 감싸야 합니다.

예:
```bash
python3 -m budget_app search --tag "meal lunch"
```

---

## 8. 거래 수정

거래 수정은 **옵션 방식**으로 구현했습니다.

```bash
python3 -m budget_app update --id <거래 ID> [수정 옵션]
```

예:

```bash
python3 -m budget_app update \
    --id TX-000001 \
    --amount 20000 \
    --memo "저녁"
```

사용 가능한 수정 옵션:

```text
--date
--type
--category
--amount
--memo
--tags
```

지정한 필드만 변경되고 지정하지 않은 필드는 기존 값이 유지됩니다.

예:

```bash
python3 -m budget_app update \
    --id TX-000001 \
    --category transport
```

태그를 모두 제거하려면 빈 문자열을 전달할 수 있습니다.

```bash
python3 -m budget_app update \
    --id TX-000001 \
    --tags ""
```

존재하지 않는 ID를 지정하면 오류가 출력됩니다.

---

## 9. 거래 삭제

```bash
python3 -m budget_app delete --id TX-000001
```

성공 예:

```text
[삭제 완료] id=TX-000001
```

존재하지 않는 거래 ID는 삭제할 수 없습니다.

---

## 10. 월별 예산 설정

```bash
python3 -m budget_app budget set \
    --month 2026-09 \
    --amount 500000
```

예:

```text
[저장 완료] 2026-09 예산 500000원
```

같은 월의 예산을 다시 설정하면 기존 예산 금액이 변경됩니다.

---

## 11. 월별 요약

```bash
python3 -m budget_app summary \
    --month 2026-09
```

기본적으로 지출 카테고리 상위 3개를 출력합니다.

```bash
python3 -m budget_app summary \
    --month 2026-09 \
    --top 5
```

출력 예:

```text
총 수입: 3000000원
총 지출: 215000원
잔액: 2785000원
예산: 500000원 (사용률 43.0%)

지출 TOP 3
1) rent 150000원
2) food 45000원
3) transport 20000원
```

설정된 예산보다 총 지출이 많으면 경고를 출력합니다.

```text
[경고] 예산을 초과했습니다.
```

해당 월에 거래 데이터가 없으면 다음과 같이 출력합니다.

```text
데이터 없음
```

---

## 12. CSV 가져오기

```bash
python3 -m budget_app import \
    --from import.csv
```

성공 예:

```text
[완료] imported=5, skipped=1
```

- `imported`: 정상적으로 등록된 거래 수
- `skipped`: 형식 오류 등으로 건너뛴 거래 수

CSV에 사용된 카테고리는 프로그램에 미리 등록되어 있어야 합니다.

---

## 13. CSV 내보내기

특정 월의 거래를 내보낼 수 있습니다.

```bash
python3 -m budget_app export \
    --out export.csv \
    --month 2026-09
```

또는 날짜 범위를 사용할 수 있습니다.

```bash
python3 -m budget_app export \
    --out export.csv \
    --from 2026-09-01 \
    --to 2026-09-30
```

완료 예:

```text
[완료] export.csv (12 records)
```

다음 조건 중 하나를 사용해야 합니다.

```text
--month
```

또는:

```text
--from + --to
```

`--month`와 `--from/--to`는 동시에 사용할 수 없습니다.

---

## 14. CSV 스키마

Import와 Export에서 사용하는 CSV 형식은 다음과 같습니다.

| column | 필수 | 설명 |
| --- | --- | --- |
| `date` | Y | `YYYY-MM-DD` |
| `type` | Y | `income` 또는 `expense` |
| `category` | Y | 등록된 카테고리 |
| `amount` | Y | 양수 정수 |
| `memo` | N | 메모 문자열 |
| `tags` | N | 쉼표(`,`)로 구분한 태그 문자열 |

공통 규칙:

- UTF-8 인코딩
- 첫 번째 행에 헤더 포함

예:

```csv
date,type,category,amount,memo,tags
2026-09-27,expense,food,20000,저녁,"meal,lunch"
2026-09-21,expense,food,15000,점심,meal
2026-09-01,income,salary,3000000,월급,salary
```

---

## 15. 입력 검증 및 오류 처리

다음과 같은 잘못된 입력을 검증합니다.

- 잘못된 날짜 형식
- 0 이하의 금액
- `income`, `expense` 이외의 거래 유형
- 존재하지 않는 카테고리
- 존재하지 않는 거래 ID
- 잘못된 조회 기간
- 잘못된 export 조건
- 잘못된 명령 옵션 및 자료형

예:

```text
[오류] 거래 날짜: YYYY-MM-DD 형식의 올바른 날짜여야 합니다.
[힌트] 입력값과 형식을 확인한 뒤 다시 시도해 주세요.
```

CLI 명령 형식 자체가 잘못된 경우에도 오류 원인과 `--help` 사용 안내를 출력합니다.

예:

```text
[오류] argument --limit: invalid int value: 'abc'
[힌트] --help 옵션으로 사용 방법을 확인해 주세요.
```

예상 가능한 애플리케이션 오류는 traceback 대신 사용자용 오류 메시지와 해결 힌트를 출력하도록 구성했습니다.

정상 실행은 종료 코드 `0`, 오류 발생 시 `0`이 아닌 종료 코드를 사용합니다.

---

## 16. 프로젝트 구조

```text
budget_app/
├── __main__.py
├── cli.py
├── decorators.py
├── errors.py
├── models.py
├── repositories.py
├── services.py
├── types_aliases.py
└── validators.py
```

각 모듈의 역할:

| 모듈 | 역할 |
| --- | --- |
| `models.py` | Transaction, Category, Budget 등의 데이터 모델 |
| `validators.py` | 입력값 파싱, 정규화 및 검증 |
| `repositories.py` | JSONL 파일 읽기/쓰기 및 영구 저장 |
| `services.py` | 거래, 카테고리, 예산, 요약, CSV 기능의 비즈니스 로직 |
| `cli.py` | 명령어 파싱, 사용자 입출력, handler 연결 |
| `errors.py` | 애플리케이션에서 예상 가능한 예외 정의 |
| `decorators.py` | CLI 공통 예외 처리를 담당하는 데코레이터 |
| `__main__.py` | `python -m budget_app` 실행 진입점 |

---

## 17. 데이터 처리 방식

Repository는 JSONL 파일 전체를 한 번에 메모리에 적재하지 않고 제너레이터를 사용해 한 줄씩 처리합니다.

이를 통해 데이터가 많아지더라도 파일 전체 크기에 비례해 메모리를 한꺼번에 사용하는 것을 피할 수 있습니다.

거래 목록과 검색 기능도 Repository에서 전달되는 iterator를 순차적으로 처리합니다.

---

## 18. 저장 안전성

거래 수정 및 삭제처럼 기존 파일 전체를 다시 작성해야 하는 작업은 임시 파일에 데이터를 먼저 기록한 뒤 원본 파일과 교체하는 방식으로 처리합니다.

따라서 파일을 직접 덮어쓰는 방식보다 작업 도중 원본 데이터가 손상될 가능성을 줄일 수 있습니다.

---

## 19. 테스트

전체 테스트 실행:

```bash
python3 -m unittest discover -s tests -v
```

CLI 테스트에서는 임시 데이터 디렉터리를 사용하므로 실제 `./data` 파일을 변경하지 않습니다.

주요 테스트 대상:

- 모델 검증
- 입력 validator
- JSONL Repository
- Service 로직
- CLI command 및 handler 연결
- 정상/오류 종료 코드
- 카테고리 관리
- 거래 추가/조회/검색/수정/삭제
- 예산 및 월별 요약
- CSV import/export
- 각 명령의 `--help`
- 잘못된 argparse 입력

---

## 20. 주요 명령 요약

```bash
# 도움말
python3 -m budget_app --help

# 카테고리 추가
python3 -m budget_app category add

# 카테고리 조회
python3 -m budget_app category list

# 카테고리 삭제
python3 -m budget_app category remove

# 거래 추가
python3 -m budget_app add

# 최근 거래 조회
python3 -m budget_app list --limit 10

# 거래 검색
python3 -m budget_app search --category food --type expense

# 거래 수정
python3 -m budget_app update --id TX-000001 --amount 20000

# 거래 삭제
python3 -m budget_app delete --id TX-000001

# 예산 설정
python3 -m budget_app budget set --month 2026-09 --amount 500000

# 월별 요약
python3 -m budget_app summary --month 2026-09 --top 3

# CSV 가져오기
python3 -m budget_app import --from import.csv

# 월 기준 CSV 내보내기
python3 -m budget_app export --out export.csv --month 2026-09

# 날짜 범위 기준 CSV 내보내기
python3 -m budget_app export \
    --out export.csv \
    --from 2026-09-01 \
    --to 2026-09-30

# 다른 데이터 디렉터리 사용
python3 -m budget_app --data-dir ./test_data list
```