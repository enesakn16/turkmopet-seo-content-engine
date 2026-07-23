from __future__ import annotations

import csv
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

from .audit import AuditIssue, AuditResult, ProductRecord, Severity, audit_product


_REQUIRED_COLUMNS = {
    "name",
    "slug",
    "meta_title",
    "meta_description",
    "description",
    "brand",
    "category",
}


class CatalogImportError(ValueError):
    """Raised when a catalog CSV cannot be safely interpreted."""


@dataclass(frozen=True, slots=True)
class CatalogAuditItem:
    row_number: int
    product: ProductRecord
    result: AuditResult


@dataclass(frozen=True, slots=True)
class CatalogAuditReport:
    items: tuple[CatalogAuditItem, ...]

    @property
    def product_count(self) -> int:
        return len(self.items)

    @property
    def issue_count(self) -> int:
        return sum(len(item.result.issues) for item in self.items)

    @property
    def average_score(self) -> float:
        if not self.items:
            return 0.0
        return round(sum(item.result.score for item in self.items) / len(self.items), 2)


def _normalized(value: str) -> str:
    return " ".join((value or "").split()).casefold()


def read_catalog_csv(path: str | Path) -> tuple[ProductRecord, ...]:
    """Read a UTF-8/Excel-compatible catalog export without changing identity fields."""
    csv_path = Path(path)
    try:
        handle = csv_path.open("r", encoding="utf-8-sig", newline="")
    except OSError as exc:
        raise CatalogImportError(f"Katalog dosyası açılamadı: {csv_path}") from exc

    with handle:
        reader = csv.DictReader(handle)
        columns = set(reader.fieldnames or ())
        missing = sorted(_REQUIRED_COLUMNS - columns)
        if missing:
            raise CatalogImportError(
                "Eksik katalog kolonları: " + ", ".join(missing)
            )

        products: list[ProductRecord] = []
        for row_number, row in enumerate(reader, start=2):
            if not any((value or "").strip() for value in row.values()):
                continue
            products.append(
                ProductRecord(
                    name=(row.get("name") or "").strip(),
                    slug=(row.get("slug") or "").strip(),
                    meta_title=(row.get("meta_title") or "").strip(),
                    meta_description=(row.get("meta_description") or "").strip(),
                    description=(row.get("description") or "").strip(),
                    brand=(row.get("brand") or "").strip(),
                    category=(row.get("category") or "").strip(),
                )
            )

    return tuple(products)


def _duplicate_indexes(values: Iterable[str]) -> set[int]:
    indexes_by_value: dict[str, list[int]] = defaultdict(list)
    for index, value in enumerate(values):
        normalized = _normalized(value)
        if normalized:
            indexes_by_value[normalized].append(index)
    return {
        index
        for indexes in indexes_by_value.values()
        if len(indexes) > 1
        for index in indexes
    }


def audit_catalog(products: Iterable[ProductRecord]) -> CatalogAuditReport:
    records = tuple(products)
    duplicate_slugs = _duplicate_indexes(product.slug for product in records)
    duplicate_titles = _duplicate_indexes(product.meta_title for product in records)
    duplicate_descriptions = _duplicate_indexes(
        product.meta_description for product in records
    )

    items: list[CatalogAuditItem] = []
    for index, product in enumerate(records):
        base_result = audit_product(product)
        issues = list(base_result.issues)

        if index in duplicate_slugs:
            issues.append(
                AuditIssue(
                    "slug.duplicate",
                    Severity.ERROR,
                    "slug",
                    "Slug katalog içinde birden fazla üründe kullanılıyor.",
                )
            )
        if index in duplicate_titles:
            issues.append(
                AuditIssue(
                    "meta_title.duplicate",
                    Severity.WARNING,
                    "meta_title",
                    "Meta başlık katalog içinde tekrar ediyor.",
                )
            )
        if index in duplicate_descriptions:
            issues.append(
                AuditIssue(
                    "meta_description.duplicate",
                    Severity.WARNING,
                    "meta_description",
                    "Meta açıklama katalog içinde tekrar ediyor.",
                )
            )

        extra_penalty = sum(
            25 if issue.severity == Severity.ERROR else 10
            for issue in issues[len(base_result.issues) :]
        )
        result = AuditResult(
            score=max(0, base_result.score - extra_penalty),
            issues=tuple(issues),
        )
        items.append(CatalogAuditItem(index + 2, product, result))

    return CatalogAuditReport(items=tuple(items))


def write_audit_csv(report: CatalogAuditReport, path: str | Path) -> None:
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=(
                "row_number",
                "name",
                "slug",
                "score",
                "passed",
                "severity",
                "field",
                "code",
                "message",
            ),
        )
        writer.writeheader()
        for item in report.items:
            if not item.result.issues:
                writer.writerow(
                    {
                        "row_number": item.row_number,
                        "name": item.product.name,
                        "slug": item.product.slug,
                        "score": item.result.score,
                        "passed": item.result.passed,
                        "severity": "",
                        "field": "",
                        "code": "",
                        "message": "",
                    }
                )
                continue
            for issue in item.result.issues:
                writer.writerow(
                    {
                        "row_number": item.row_number,
                        "name": item.product.name,
                        "slug": item.product.slug,
                        "score": item.result.score,
                        "passed": item.result.passed,
                        "severity": issue.severity.value,
                        "field": issue.field,
                        "code": issue.code,
                        "message": issue.message,
                    }
                )
