from __future__ import annotations

import argparse
import sys
from collections.abc import Sequence
from pathlib import Path

from .adapters import read_platform_catalog_csv
from .catalog import CatalogImportError, audit_catalog, read_catalog_csv
from .search_console import (
    SearchConsoleImportError,
    prioritize_search_opportunities,
    read_search_console_csv,
    write_search_opportunities_csv,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="seo-opportunities",
        description=(
            "Katalog SEO denetimini Search Console verisiyle birleştirip "
            "ürün bazlı trafik fırsatı raporu üretir."
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
    parser.add_argument("--output", required=True, type=Path, help="Çıktı CSV dosyası")
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

    print(
        f"{report.product_count} ürün analiz edildi; "
        f"{len(opportunities)} trafik fırsatı {args.output} dosyasına yazıldı."
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
