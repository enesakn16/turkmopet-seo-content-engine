from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable
from urllib.parse import unquote, urlparse

from .search_console import SearchConsoleRow


@dataclass(frozen=True, slots=True)
class CannibalizationPage:
    page: str
    slug: str
    clicks: int
    impressions: int
    ctr: float
    average_position: float


@dataclass(frozen=True, slots=True)
class CannibalizationConflict:
    query: str
    page_count: int
    total_clicks: int
    total_impressions: int
    leading_page: str
    leading_share: float
    severity: str
    action_type: str
    recommended_action: str
    pages: tuple[CannibalizationPage, ...]


def _normalized_query(value: str) -> str:
    return " ".join((value or "").strip().casefold().split())


def _normalized_page(value: str) -> str:
    parsed = urlparse((value or "").strip())
    path = unquote(parsed.path).rstrip("/") or "/"
    normalized_path = path.casefold()
    if parsed.netloc:
        return f"{parsed.netloc.casefold()}{normalized_path}"
    return normalized_path


def _slug(page: str) -> str:
    return page.rstrip("/").rsplit("/", 1)[-1] or "/"


def _recommended_action(
    *, page_count: int, leading_share: float, leading_page: str
) -> tuple[str, str]:
    if leading_share < 0.60 or (page_count >= 3 and leading_share < 0.80):
        return (
            "consolidate_or_canonical_review",
            "Sayfaların arama niyetini karşılaştır; aynı amacı taşıyanları birleştir veya canonical kararını doğrula.",
        )
    if leading_share < 0.80:
        return (
            "separate_search_intent",
            "Lider ve ikincil sayfaların başlık, içerik ve iç bağlantılarını farklı arama niyetlerine göre ayrıştır.",
        )
    return (
        "strengthen_leading_page",
        f"İç bağlantıları {leading_page} adresine yoğunlaştır ve ikincil URL'nin sorguyla gereksiz eşleşmesini incele.",
    )


def detect_cannibalization(
    rows: Iterable[SearchConsoleRow],
    *,
    minimum_impressions: int = 50,
    minimum_pages: int = 2,
    minimum_page_impressions: int = 10,
) -> tuple[CannibalizationConflict, ...]:
    if minimum_impressions < 1:
        raise ValueError("minimum_impressions en az 1 olmalıdır.")
    if minimum_pages < 2:
        raise ValueError("minimum_pages en az 2 olmalıdır.")
    if minimum_page_impressions < 1:
        raise ValueError("minimum_page_impressions en az 1 olmalıdır.")
    if minimum_page_impressions > minimum_impressions:
        raise ValueError(
            "minimum_page_impressions, minimum_impressions değerinden büyük olamaz."
        )

    grouped: dict[str, dict[str, list[SearchConsoleRow]]] = {}
    labels: dict[str, str] = {}
    for row in rows:
        query_key = _normalized_query(row.query)
        page_key = _normalized_page(row.page)
        if not query_key or not page_key or row.impressions <= 0:
            continue
        labels.setdefault(query_key, " ".join(row.query.strip().split()))
        grouped.setdefault(query_key, {}).setdefault(page_key, []).append(row)

    conflicts: list[CannibalizationConflict] = []
    for query_key, page_rows in grouped.items():
        page_metrics: list[CannibalizationPage] = []
        for page, values in page_rows.items():
            impressions = sum(item.impressions for item in values)
            if impressions < minimum_page_impressions:
                continue
            clicks = sum(item.clicks for item in values)
            weighted_position = sum(item.position * item.impressions for item in values) / impressions
            page_metrics.append(CannibalizationPage(
                page=page,
                slug=_slug(page),
                clicks=clicks,
                impressions=impressions,
                ctr=round(clicks / impressions, 4),
                average_position=round(weighted_position, 2),
            ))

        total_impressions = sum(item.impressions for item in page_metrics)
        if len(page_metrics) < minimum_pages or total_impressions < minimum_impressions:
            continue

        page_metrics.sort(key=lambda item: (-item.impressions, -item.clicks, item.average_position, item.page))
        leader = page_metrics[0]
        leading_share = leader.impressions / total_impressions
        if leading_share < 0.60:
            severity = "critical"
        elif leading_share < 0.80:
            severity = "warning"
        else:
            severity = "review"
        action_type, recommended_action = _recommended_action(
            page_count=len(page_metrics),
            leading_share=leading_share,
            leading_page=leader.page,
        )

        conflicts.append(CannibalizationConflict(
            query=labels[query_key],
            page_count=len(page_metrics),
            total_clicks=sum(item.clicks for item in page_metrics),
            total_impressions=total_impressions,
            leading_page=leader.page,
            leading_share=round(leading_share, 4),
            severity=severity,
            action_type=action_type,
            recommended_action=recommended_action,
            pages=tuple(page_metrics),
        ))

    severity_order = {"critical": 0, "warning": 1, "review": 2}
    return tuple(sorted(
        conflicts,
        key=lambda item: (severity_order[item.severity], -item.total_impressions, item.query.casefold()),
    ))


def write_cannibalization_csv(
    conflicts: Iterable[CannibalizationConflict], path: str | Path
) -> None:
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    fields = (
        "query", "severity", "action_type", "recommended_action", "page_count",
        "total_clicks", "total_impressions", "leading_page", "leading_share", "page",
        "slug", "clicks", "impressions", "ctr", "average_position",
    )
    with output.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for conflict in conflicts:
            for page in conflict.pages:
                writer.writerow({
                    "query": conflict.query,
                    "severity": conflict.severity,
                    "action_type": conflict.action_type,
                    "recommended_action": conflict.recommended_action,
                    "page_count": conflict.page_count,
                    "total_clicks": conflict.total_clicks,
                    "total_impressions": conflict.total_impressions,
                    "leading_page": conflict.leading_page,
                    "leading_share": conflict.leading_share,
                    "page": page.page,
                    "slug": page.slug,
                    "clicks": page.clicks,
                    "impressions": page.impressions,
                    "ctr": page.ctr,
                    "average_position": page.average_position,
                })
