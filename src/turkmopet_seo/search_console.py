from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable
from urllib.parse import unquote, urlparse

from .catalog import CatalogAuditReport


class SearchConsoleImportError(ValueError):
    pass


@dataclass(frozen=True, slots=True)
class SearchConsoleRow:
    query: str
    page: str
    clicks: int
    impressions: int
    ctr: float
    position: float


@dataclass(frozen=True, slots=True)
class ProductSearchOpportunity:
    row_number: int
    name: str
    slug: str
    audit_score: int
    clicks: int
    impressions: int
    ctr: float
    average_position: float
    query_count: int
    top_query: str
    opportunity_score: float


_ALIASES = {
    "query": ("query", "sorgu"),
    "page": ("page", "sayfa"),
    "clicks": ("clicks", "tıklamalar", "tiklamalar"),
    "impressions": ("impressions", "gösterimler", "gosterimler"),
    "ctr": ("ctr", "to"),
    "position": ("position", "average position", "konum", "ortalama konum"),
}


def _header(value: str) -> str:
    return " ".join((value or "").strip().casefold().split())


def _columns(fieldnames: Iterable[str]) -> dict[str, str]:
    available = {_header(name): name for name in fieldnames}
    result = {
        key: next((available[_header(alias)] for alias in aliases if _header(alias) in available), "")
        for key, aliases in _ALIASES.items()
    }
    missing = sorted(key for key, value in result.items() if not value)
    if missing:
        raise SearchConsoleImportError("Eksik Search Console kolonları: " + ", ".join(missing))
    return result


def _number(value: str, row_number: int, field: str) -> float:
    cleaned = (value or "").strip().replace("%", "").replace(",", ".")
    try:
        return float(cleaned)
    except ValueError as exc:
        raise SearchConsoleImportError(
            f"{row_number}. satırda geçersiz {field}: {value!r}"
        ) from exc


def read_search_console_csv(path: str | Path) -> tuple[SearchConsoleRow, ...]:
    csv_path = Path(path)
    try:
        handle = csv_path.open("r", encoding="utf-8-sig", newline="")
    except OSError as exc:
        raise SearchConsoleImportError(f"Dosya açılamadı: {csv_path}") from exc
    with handle:
        reader = csv.DictReader(handle)
        columns = _columns(reader.fieldnames or ())
        rows: list[SearchConsoleRow] = []
        for row_number, row in enumerate(reader, start=2):
            if not any((value or "").strip() for value in row.values()):
                continue
            clicks = int(_number(row[columns["clicks"]], row_number, "clicks"))
            impressions = int(_number(row[columns["impressions"]], row_number, "impressions"))
            ctr_raw = _number(row[columns["ctr"]], row_number, "ctr")
            ctr = ctr_raw / 100 if ctr_raw > 1 else ctr_raw
            position = _number(row[columns["position"]], row_number, "position")
            if clicks < 0 or impressions < 0 or not 0 <= ctr <= 1 or position < 0:
                raise SearchConsoleImportError(f"{row_number}. satırda metrik aralığı geçersiz.")
            rows.append(SearchConsoleRow(
                query=(row[columns["query"]] or "").strip(),
                page=(row[columns["page"]] or "").strip(),
                clicks=clicks,
                impressions=impressions,
                ctr=ctr,
                position=position,
            ))
    return tuple(rows)


def _slug(page: str) -> str:
    path = unquote(urlparse(page).path).rstrip("/")
    return path.rsplit("/", 1)[-1].strip().casefold()


def prioritize_search_opportunities(
    report: CatalogAuditReport,
    search_rows: Iterable[SearchConsoleRow],
) -> tuple[ProductSearchOpportunity, ...]:
    by_slug: dict[str, list[SearchConsoleRow]] = {}
    for row in search_rows:
        by_slug.setdefault(_slug(row.page), []).append(row)
    opportunities: list[ProductSearchOpportunity] = []
    for item in report.items:
        matched = by_slug.get(item.product.slug.strip().casefold(), [])
        impressions = sum(row.impressions for row in matched)
        if not matched or impressions <= 0:
            continue
        clicks = sum(row.clicks for row in matched)
        ctr = clicks / impressions
        position = sum(row.position * row.impressions for row in matched) / impressions
        ranking_factor = 0.6 if position <= 3 else 1.0 if position <= 20 else 0.4
        quality_factor = 0.5 + (100 - item.result.score) / 100
        top_query = max(matched, key=lambda row: (row.impressions, row.clicks)).query
        opportunities.append(ProductSearchOpportunity(
            row_number=item.row_number,
            name=item.product.name,
            slug=item.product.slug,
            audit_score=item.result.score,
            clicks=clicks,
            impressions=impressions,
            ctr=round(ctr, 4),
            average_position=round(position, 2),
            query_count=len({row.query.casefold() for row in matched if row.query}),
            top_query=top_query,
            opportunity_score=round(impressions * (1 - ctr) * ranking_factor * quality_factor, 2),
        ))
    return tuple(sorted(opportunities, key=lambda item: (-item.opportunity_score, item.audit_score, item.slug)))


def write_search_opportunities_csv(
    opportunities: Iterable[ProductSearchOpportunity], path: str | Path
) -> None:
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    fields = tuple(ProductSearchOpportunity.__dataclass_fields__)
    with output.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for item in opportunities:
            writer.writerow({field: getattr(item, field) for field in fields})
