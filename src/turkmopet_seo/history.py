from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Mapping


class ManifestComparisonError(ValueError):
    """Raised when a run manifest cannot be compared safely."""


@dataclass(frozen=True, slots=True)
class MetricDelta:
    previous: float
    current: float

    @property
    def change(self) -> float:
        return round(self.current - self.previous, 2)


@dataclass(frozen=True, slots=True)
class ManifestComparison:
    average_score: MetricDelta
    issue_count: MetricDelta
    traffic_opportunity_count: MetricDelta
    product_count: MetricDelta
    regressions: tuple[str, ...]

    @property
    def has_regression(self) -> bool:
        return bool(self.regressions)


def read_run_manifest(path: str | Path) -> dict[str, object]:
    """Read and validate the minimum manifest contract used for comparisons."""
    source = Path(path)
    try:
        data = json.loads(source.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ManifestComparisonError(f"Manifest okunamadı: {source}") from exc

    if not isinstance(data, dict):
        raise ManifestComparisonError("Manifest kök değeri JSON nesnesi olmalıdır")
    if data.get("schema_version") != 1:
        raise ManifestComparisonError("Yalnızca schema_version=1 manifestleri desteklenir")
    metrics = data.get("metrics")
    if not isinstance(metrics, dict):
        raise ManifestComparisonError("Manifest metrics nesnesi içermelidir")
    _extract_metrics(metrics)
    return data


def compare_run_manifests(
    previous: Mapping[str, object],
    current: Mapping[str, object],
    *,
    minimum_score_change: float = 0.0,
    maximum_issue_increase: int = 0,
) -> ManifestComparison:
    """Compare two successful v1 manifests and identify SEO regressions."""
    if minimum_score_change < 0:
        raise ValueError("minimum_score_change negatif olamaz")
    if maximum_issue_increase < 0:
        raise ValueError("maximum_issue_increase negatif olamaz")

    previous_metrics = _manifest_metrics(previous)
    current_metrics = _manifest_metrics(current)

    score = MetricDelta(previous_metrics["average_score"], current_metrics["average_score"])
    issues = MetricDelta(previous_metrics["issue_count"], current_metrics["issue_count"])
    opportunities = MetricDelta(
        previous_metrics["traffic_opportunity_count"],
        current_metrics["traffic_opportunity_count"],
    )
    products = MetricDelta(previous_metrics["product_count"], current_metrics["product_count"])

    regressions: list[str] = []
    if score.change < -minimum_score_change:
        regressions.append("average_score_decreased")
    if issues.change > maximum_issue_increase:
        regressions.append("issue_count_increased")

    return ManifestComparison(
        average_score=score,
        issue_count=issues,
        traffic_opportunity_count=opportunities,
        product_count=products,
        regressions=tuple(regressions),
    )


def write_manifest_comparison(
    comparison: ManifestComparison,
    path: str | Path,
) -> None:
    """Write a deterministic JSON comparison for dashboards and automation."""
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "status": "regression" if comparison.has_regression else "success",
        "regressions": list(comparison.regressions),
        "metrics": {
            "average_score": _delta_payload(comparison.average_score),
            "issue_count": _delta_payload(comparison.issue_count),
            "product_count": _delta_payload(comparison.product_count),
            "traffic_opportunity_count": _delta_payload(
                comparison.traffic_opportunity_count
            ),
        },
    }
    output.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def _manifest_metrics(manifest: Mapping[str, object]) -> dict[str, float]:
    if manifest.get("schema_version") != 1:
        raise ManifestComparisonError("Yalnızca schema_version=1 manifestleri desteklenir")
    if manifest.get("status") != "success":
        raise ManifestComparisonError("Yalnızca başarılı manifestler karşılaştırılabilir")
    metrics = manifest.get("metrics")
    if not isinstance(metrics, Mapping):
        raise ManifestComparisonError("Manifest metrics nesnesi içermelidir")
    return _extract_metrics(metrics)


def _extract_metrics(metrics: Mapping[str, object]) -> dict[str, float]:
    required = (
        "average_score",
        "issue_count",
        "product_count",
        "traffic_opportunity_count",
    )
    result: dict[str, float] = {}
    for name in required:
        value = metrics.get(name)
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise ManifestComparisonError(f"Geçersiz veya eksik metrik: {name}")
        result[name] = float(value)
    return result


def _delta_payload(delta: MetricDelta) -> dict[str, float]:
    return {
        "previous": delta.previous,
        "current": delta.current,
        "change": delta.change,
    }
