import json
import tempfile
import unittest
from pathlib import Path

from turkmopet_seo.history import (
    ManifestComparisonError,
    compare_run_manifests,
    read_run_manifest,
    write_manifest_comparison,
)


def manifest(*, score=70.0, issues=10, products=20, opportunities=4):
    return {
        "schema_version": 1,
        "status": "success",
        "metrics": {
            "average_score": score,
            "issue_count": issues,
            "product_count": products,
            "traffic_opportunity_count": opportunities,
        },
    }


class ManifestHistoryTests(unittest.TestCase):
    def test_reports_improvements_without_regression(self):
        result = compare_run_manifests(
            manifest(),
            manifest(score=74.5, issues=7, opportunities=6),
        )

        self.assertFalse(result.has_regression)
        self.assertEqual(result.average_score.change, 4.5)
        self.assertEqual(result.issue_count.change, -3.0)
        self.assertEqual(result.traffic_opportunity_count.change, 2.0)

    def test_detects_score_and_issue_regressions(self):
        result = compare_run_manifests(
            manifest(score=80, issues=5),
            manifest(score=76, issues=9),
        )

        self.assertTrue(result.has_regression)
        self.assertEqual(
            result.regressions,
            ("average_score_decreased", "issue_count_increased"),
        )

    def test_applies_regression_tolerances(self):
        result = compare_run_manifests(
            manifest(score=80, issues=5),
            manifest(score=79.5, issues=6),
            minimum_score_change=1.0,
            maximum_issue_increase=2,
        )

        self.assertFalse(result.has_regression)

    def test_rejects_failed_or_unknown_schema_manifest(self):
        failed = manifest()
        failed["status"] = "failed"
        with self.assertRaises(ManifestComparisonError):
            compare_run_manifests(failed, manifest())

        unknown = manifest()
        unknown["schema_version"] = 2
        with self.assertRaises(ManifestComparisonError):
            compare_run_manifests(manifest(), unknown)

    def test_reads_and_validates_manifest_file(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "manifest.json"
            path.write_text(json.dumps(manifest()), encoding="utf-8")
            result = read_run_manifest(path)

        self.assertEqual(result["schema_version"], 1)

    def test_writes_deterministic_comparison_json(self):
        result = compare_run_manifests(
            manifest(score=80, issues=5),
            manifest(score=78, issues=8),
        )
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "nested" / "comparison.json"
            write_manifest_comparison(result, path)
            payload = json.loads(path.read_text(encoding="utf-8"))

        self.assertEqual(payload["status"], "regression")
        self.assertEqual(payload["metrics"]["average_score"]["change"], -2.0)
        self.assertEqual(payload["metrics"]["issue_count"]["change"], 3.0)


if __name__ == "__main__":
    unittest.main()
