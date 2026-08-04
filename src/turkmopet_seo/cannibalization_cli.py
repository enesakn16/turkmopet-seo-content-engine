from __future__ import annotations

import argparse

from .cannibalization import detect_cannibalization, write_cannibalization_csv
from .search_console import SearchConsoleImportError, read_search_console_csv


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Search Console verisinden anahtar kelime kanibalizasyon raporu üretir."
    )
    parser.add_argument("--input", required=True, help="Search Console CSV dosyası")
    parser.add_argument("--output", required=True, help="Çıktı CSV dosyası")
    parser.add_argument("--minimum-impressions", type=int, default=50)
    parser.add_argument("--minimum-pages", type=int, default=2)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        rows = read_search_console_csv(args.input)
        conflicts = detect_cannibalization(
            rows,
            minimum_impressions=args.minimum_impressions,
            minimum_pages=args.minimum_pages,
        )
        write_cannibalization_csv(conflicts, args.output)
    except (SearchConsoleImportError, ValueError) as exc:
        print(f"Hata: {exc}")
        return 2

    critical = sum(item.severity == "critical" for item in conflicts)
    print(
        f"{len(conflicts)} sorgu çakışması bulundu; "
        f"{critical} kritik. Rapor: {args.output}"
    )
    return 1 if conflicts else 0


if __name__ == "__main__":
    raise SystemExit(main())
