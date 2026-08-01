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


def manifest(*, score=70.0, issues=10, products=20, opportunities=4, groups=None):
    payload = {
        "schema_version": 1,
        "status": "success",
        "metrics": {
            "average_score": score,
            "issue_count": issues,
            "product_count": products,
            "traffic_opportunity_count": opportunities,
        },
    }
    if groups is not None:
        payload["groups"] = groups
    return payload


def group_metrics(*, tvs_score=80.0, tvs_issues=3, fren_score=75.0, fren_issues=4):
    return {
        "brands": [
            {
                "name": "TVS",
                "product_count": 10,
                "failed_count": 2,
                "issue_count": tvs_issues,
                "average_score": tvs_score,
            }
        ],
        "categories": [
            {
                "name": "Fren",
                "product_count": 8,
                "failed_count": 3,
                "issue_count": fren_issues,
                "average_score": fren_score,
            }
        ],
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

    def test_detects_and_prioritizes_brand_and_category_regressions(self):
        result = compare_run_manifests(
            manifest(groups=group_metrics()),
            manifest(
                groups=group_metrics(
                    tvs_score=72.0,
                    tvs_issues=7,
                    fren_score=76.0,
                    fren_issues=3,
                )
            ),
        )

        self.assertTrue(result.has_regression)
        self.assertEqual(result.group_comparisons[0].dimension, "brand")
        self.assertEqual(result.group_comparisons[0].name, "TVS")
        self.assertEqual(result.group_comparisons[0].average_score.change, -8.0)
        self.assertEqual(
            result.group_comparisons[0].regressions,
            ("average_score_decreased", "issue_count_increased"),
        )
        self.assertIn("brand:TVS:average_score_decreased", result.regressions)
        self.assertIn("brand:TVS:issue_count_increased", result.regressions)
        self.assertFalse(result.group_comparisons[1].has_regression)

    def test_applies_regression_tolerances_to_groups(self):
        result = compare_run_manifests(
            manifest(groups=group_metrics()),
            manifest(groups=group_metrics(tvs_score=79.5, tvs_issues=4)),
            minimum_score_change=1.0,
            maximum_issue_increase=2,
        )

        self.assertFalse(result.has_regression)

    def test_rejects_duplicate_group_entries(self):
        groups = group_metrics()
        groups["brands"].append(dict(groups["brands"][0]))
        with self.assertRaisesRegex(ManifestComparisonError, "Tekrarlı grup"):
            compare_run_manifests(manifest(groups=groups), manifest(groups=group_metrics()))

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
            path.write_text(json.dumps(manifest(groups=group_metrics())), encoding="utf-8")
            result = read_run_manifest(path)

        self.assertEqual(result["schema_version"], 1)

    def test_writes_deterministic_comparison_json_with_group_details(self):
        result = compare_run_manifests(
            manifest(score=80, issues=5, groups=group_metrics()),
            manifest(
                score=78,
                issues=8,
                groups=group_metrics(tvs_score=70, tvs_issues=8),
            ),
        )
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "nested" / "comparison.json"
            write_manifest_comparison(result, path)
            payload = json.loads(path.read_text(encoding="utf-8"))

        self.assertEqual(payload["status"], "regression")
        self.assertEqual(payload["metrics"]["average_score"]["change"], -2.0)
        self.assertEqual(payload["metrics"]["issue_count"]["change"], 3.0)
        self.assertEqual(payload["groups"][0]["name"], "TVS")
        self.assertEqual(payload["groups"][0]["average_score"]["change"], -10.0)


if __name__ == "__main__":
    unittest.main()
