from __future__ import annotations

import argparse
import sys
from collections.abc import Sequence
from pathlib import Path

from .history import (
    ManifestComparisonError,
    compare_run_manifests,
    read_run_manifest,
    write_manifest_comparison,
)


REGRESSION_EXIT_CODE = 3


def _non_negative_float(value: str) -> float:
    try:
        parsed = float(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError("sayı olmalıdır") from exc
    if parsed < 0:
        raise argparse.ArgumentTypeError("sıfırdan küçük olamaz")
    return parsed


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
        prog="seo-compare-runs",
        description=(
            "İki SEO çalışma manifestini karşılaştırır, metrik değişimlerini JSON olarak "
            "yazar ve isteğe bağlı olarak regresyonda başarısız çıkış kodu döndürür."
        ),
    )
    parser.add_argument("--previous", required=True, type=Path, help="Önceki çalışma manifesti")
    parser.add_argument("--current", required=True, type=Path, help="Güncel çalışma manifesti")
    parser.add_argument("--output", required=True, type=Path, help="Karşılaştırma JSON çıktısı")
    parser.add_argument(
        "--minimum-score-change",
        type=_non_negative_float,
        default=0.0,
        help="Regresyon sayılmayacak azami SEO puanı düşüşü (varsayılan: 0)",
    )
    parser.add_argument(
        "--maximum-issue-increase",
        type=_non_negative_int,
        default=0,
        help="Regresyon sayılmayacak azami sorun artışı (varsayılan: 0)",
    )
    parser.add_argument(
        "--fail-on-regression",
        action="store_true",
        help=f"Regresyon varsa {REGRESSION_EXIT_CODE} çıkış kodu döndür",
    )
    return parser


def run(args: argparse.Namespace) -> int:
    previous = read_run_manifest(args.previous)
    current = read_run_manifest(args.current)
    comparison = compare_run_manifests(
        previous,
        current,
        minimum_score_change=args.minimum_score_change,
        maximum_issue_increase=args.maximum_issue_increase,
    )
    write_manifest_comparison(comparison, args.output)

    status = "REGRESSION" if comparison.has_regression else "SUCCESS"
    print(
        f"{status}: SEO puanı {comparison.average_score.change:+.2f}, "
        f"sorun sayısı {comparison.issue_count.change:+.0f}, "
        f"trafik fırsatı {comparison.traffic_opportunity_count.change:+.0f}. "
        f"Rapor: {args.output}"
    )
    if args.fail_on_regression and comparison.has_regression:
        return REGRESSION_EXIT_CODE
    return 0


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        return run(args)
    except ManifestComparisonError as exc:
        print(f"Hata: {exc}", file=sys.stderr)
        return 2
    except OSError as exc:
        print(f"Dosya hatası: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
