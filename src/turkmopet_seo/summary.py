from __future__ import annotations

import csv
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path

from .audit import Severity
from .catalog import CatalogAuditItem, CatalogAuditReport


_SEVERITY_RANK = {
    Severity.INFO: 1,
    Severity.WARNING: 2,
    Severity.ERROR: 3,
}


@dataclass(frozen=True, slots=True)
class CatalogGroupSummary:
    dimension: str
    name: str
    product_count: int
    failed_count: int
    issue_count: int
    average_score: float


@dataclass(frozen=True, slots=True)
class CatalogPriorityItem:
    row_number: int
    name: str
    slug: str
    brand: str
    category: str
    score: int
    issue_count: int
    highest_severity: str


@dataclass(frozen=True, slots=True)
class CatalogSummary:
    brands: tuple[CatalogGroupSummary, ...]
    categories: tuple[CatalogGroupSummary, ...]
    priorities: tuple[CatalogPriorityItem, ...]
    issue_codes: tuple[tuple[str, int], ...]


def _group_items(
    items: tuple[CatalogAuditItem, ...],
    dimension: str,
) -> tuple[CatalogGroupSummary, ...]:
    grouped: dict[str, list[CatalogAuditItem]] = defaultdict(list)
    for item in items:
        raw_name = getattr(item.product, dimension).strip()
        grouped[raw_name or "(belirtilmemiş)"].append(item)

    summaries = []
    for name, group in grouped.items():
        summaries.append(
            CatalogGroupSummary(
                dimension=dimension,
                name=name,
                product_count=len(group),
                failed_count=sum(not item.result.passed for item in group),
                issue_count=sum(len(item.result.issues) for item in group),
                average_score=round(
                    sum(item.result.score for item in group) / len(group),
                    2,
                ),
            )
        )

    return tuple(
        sorted(
            summaries,
            key=lambda item: (
                item.average_score,
                -item.issue_count,
                item.name.casefold(),
            ),
        )
    )


def _priority_item(item: CatalogAuditItem) -> CatalogPriorityItem:
    highest = max(
        (issue.severity for issue in item.result.issues),
        key=lambda severity: _SEVERITY_RANK[severity],
        default=None,
    )
    return CatalogPriorityItem(
        row_number=item.row_number,
        name=item.product.name,
        slug=item.product.slug,
        brand=item.product.brand,
        category=item.product.category,
        score=item.result.score,
        issue_count=len(item.result.issues),
        highest_severity=highest.value if highest else "",
    )


def summarize_catalog(
    report: CatalogAuditReport,
    *,
    priority_limit: int = 50,
) -> CatalogSummary:
    """Build deterministic brand, category and product-level priority summaries."""
    if priority_limit < 0:
        raise ValueError("priority_limit sıfırdan küçük olamaz")

    priorities = sorted(
        (_priority_item(item) for item in report.items if item.result.issues),
        key=lambda item: (
            item.score,
            -_severity_value(item.highest_severity),
            -item.issue_count,
            item.name.casefold(),
            item.row_number,
        ),
    )
    issue_counts = Counter(
        issue.code
        for item in report.items
        for issue in item.result.issues
    )

    return CatalogSummary(
        brands=_group_items(report.items, "brand"),
        categories=_group_items(report.items, "category"),
        priorities=tuple(priorities[:priority_limit]),
        issue_codes=tuple(sorted(issue_counts.items(), key=lambda pair: (-pair[1], pair[0]))),
    )


def _severity_value(value: str) -> int:
    for severity, rank in _SEVERITY_RANK.items():
        if severity.value == value:
            return rank
    return 0


def write_group_summary_csv(summary: CatalogSummary, path: str | Path) -> None:
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=(
                "dimension",
                "name",
                "product_count",
                "failed_count",
                "issue_count",
                "average_score",
            ),
        )
        writer.writeheader()
        for item in (*summary.brands, *summary.categories):
            writer.writerow(
                {
                    "dimension": item.dimension,
                    "name": item.name,
                    "product_count": item.product_count,
                    "failed_count": item.failed_count,
                    "issue_count": item.issue_count,
                    "average_score": item.average_score,
                }
            )


def write_priority_csv(summary: CatalogSummary, path: str | Path) -> None:
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=(
                "row_number",
                "name",
                "slug",
                "brand",
                "category",
                "score",
                "issue_count",
                "highest_severity",
            ),
        )
        writer.writeheader()
        for item in summary.priorities:
            writer.writerow(
                {
                    "row_number": item.row_number,
                    "name": item.name,
                    "slug": item.slug,
                    "brand": item.brand,
                    "category": item.category,
                    "score": item.score,
                    "issue_count": item.issue_count,
                    "highest_severity": item.highest_severity,
                }
            )
