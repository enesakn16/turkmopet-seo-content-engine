from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Mapping

from .catalog import CatalogAuditReport
from .search_console import ProductSearchOpportunity
from .summary import CatalogGroupSummary, summarize_catalog


MANIFEST_SCHEMA_VERSION = 1


def build_run_manifest(
    *,
    catalog_path: str | Path,
    platform: str,
    search_console_path: str | Path,
    report: CatalogAuditReport,
    opportunities: tuple[ProductSearchOpportunity, ...],
    outputs: Mapping[str, str | Path],
    generated_at: datetime | None = None,
) -> dict[str, object]:
    """Build a stable summary for automation and dashboard consumers."""
    timestamp = generated_at or datetime.now(timezone.utc)
    if timestamp.tzinfo is None:
        raise ValueError("generated_at saat dilimi bilgisi içermelidir")

    normalized_outputs = {
        name: str(Path(path))
        for name, path in sorted(outputs.items())
    }
    summary = summarize_catalog(report, priority_limit=0)
    return {
        "schema_version": MANIFEST_SCHEMA_VERSION,
        "status": "success",
        "generated_at": timestamp.astimezone(timezone.utc).isoformat().replace("+00:00", "Z"),
        "inputs": {
            "catalog": str(Path(catalog_path)),
            "platform": platform,
            "search_console": str(Path(search_console_path)),
        },
        "metrics": {
            "product_count": report.product_count,
            "issue_count": report.issue_count,
            "average_score": report.average_score,
            "traffic_opportunity_count": len(opportunities),
        },
        "groups": {
            "brands": [_group_payload(item) for item in summary.brands],
            "categories": [_group_payload(item) for item in summary.categories],
        },
        "outputs": normalized_outputs,
    }


def write_run_manifest(manifest: Mapping[str, object], path: str | Path) -> None:
    """Write an UTF-8 JSON manifest only after the report bundle succeeds."""
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def _group_payload(item: CatalogGroupSummary) -> dict[str, object]:
    return {
        "name": item.name,
        "product_count": item.product_count,
        "failed_count": item.failed_count,
        "issue_count": item.issue_count,
        "average_score": item.average_score,
    }
