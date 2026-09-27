from budget_app.cli_parser import build_parser
from budget_app.decorators import handle_cli_errors
from budget_app.dependencies import build_services


@handle_cli_errors
def main() -> int:
    parser = build_parser()

    args = parser.parse_args()

    services = build_services(
        args.data_dir
    )

    args.handler(
        args,
        services,
    )

    return 0