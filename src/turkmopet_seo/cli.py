from __future__ import annotations

import argparse
import sys
from collections.abc import Sequence
from pathlib import Path

from .adapters import read_platform_catalog_csv
from .catalog import CatalogImportError, audit_catalog, read_catalog_csv, write_audit_csv
from .search_console import (
    SearchConsoleImportError,
    prioritize_search_opportunities,
    read_search_console_csv,
    write_search_opportunities_csv,
)
from .suggestions import suggest_catalog_improvements, write_suggestions_csv
from .summary import summarize_catalog, write_group_summary_csv, write_priority_csv


def _non_negative_int(value: str) -> int:
    try:
        parsed = int(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError("tam sayı olmalıdır") from exc
    if parsed < 0:
        raise argparse.ArgumentTypeError("sıfırdan küçük olamaz")
    return parsed


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="seo-opportunities",
        description=(
            "Katalog SEO denetimini Search Console verisiyle birleştirip "
            "ürün bazlı trafik fırsatı ve isteğe bağlı operasyon raporları üretir."
        ),
    )
    parser.add_argument("--catalog", required=True, type=Path, help="Katalog CSV dosyası")
    parser.add_argument(
        "--platform",
        required=True,
        choices=("ikas", "shopify", "standard"),
        help="Katalog dışa aktarım biçimi",
    )
    parser.add_argument(
        "--search-console",
        required=True,
        type=Path,
        help="Search Console sorgu CSV dosyası",
    )
    parser.add_argument("--output", required=True, type=Path, help="Trafik fırsatı CSV dosyası")
    parser.add_argument(
        "--audit-output",
        type=Path,
        help="İsteğe bağlı detaylı katalog denetim CSV dosyası",
    )
    parser.add_argument(
        "--suggestions-output",
        type=Path,
        help="İsteğe bağlı insan onaylı SEO öneri CSV dosyası",
    )
    parser.add_argument(
        "--group-summary-output",
        type=Path,
        help="İsteğe bağlı marka ve kategori özet CSV dosyası",
    )
    parser.add_argument(
        "--priority-output",
        type=Path,
        help="İsteğe bağlı öncelikli ürün kuyruğu CSV dosyası",
    )
    parser.add_argument(
        "--priority-limit",
        type=_non_negative_int,
        default=50,
        help="Öncelikli ürün raporundaki azami ürün sayısı (varsayılan: 50)",
    )
    return parser


def run(args: argparse.Namespace) -> int:
    if args.platform == "standard":
        products = read_catalog_csv(args.catalog)
    else:
        products = read_platform_catalog_csv(args.catalog, args.platform)

    report = audit_catalog(products)
    search_rows = read_search_console_csv(args.search_console)
    opportunities = prioritize_search_opportunities(report, search_rows)
    write_search_opportunities_csv(opportunities, args.output)

    written_reports = [f"trafik fırsatı: {args.output}"]

    if args.audit_output:
        write_audit_csv(report, args.audit_output)
        written_reports.append(f"denetim: {args.audit_output}")

    if args.suggestions_output:
        suggestions = suggest_catalog_improvements(report)
        write_suggestions_csv(suggestions, args.suggestions_output)
        written_reports.append(f"öneri: {args.suggestions_output}")

    if args.group_summary_output or args.priority_output:
        summary = summarize_catalog(report, priority_limit=args.priority_limit)
        if args.group_summary_output:
            write_group_summary_csv(summary, args.group_summary_output)
            written_reports.append(f"grup özeti: {args.group_summary_output}")
        if args.priority_output:
            write_priority_csv(summary, args.priority_output)
            written_reports.append(f"öncelik: {args.priority_output}")

    print(
        f"{report.product_count} ürün analiz edildi; "
        f"{len(opportunities)} trafik fırsatı bulundu. "
        + " | ".join(written_reports)
    )
    return 0


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        return run(args)
    except (CatalogImportError, SearchConsoleImportError) as exc:
        print(f"Hata: {exc}", file=sys.stderr)
        return 2
    except OSError as exc:
        print(f"Dosya hatası: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
