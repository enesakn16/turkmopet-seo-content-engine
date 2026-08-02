import json
import tempfile
import unittest
from pathlib import Path

from turkmopet_seo.comparison_cli import REGRESSION_EXIT_CODE, main


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


class ManifestComparisonCliTests(unittest.TestCase):
    def _write_manifest(self, root: Path, name: str, payload: dict) -> Path:
        path = root / name
        path.write_text(json.dumps(payload), encoding="utf-8")
        return path

    def test_writes_successful_comparison(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            previous = self._write_manifest(root, "previous.json", manifest())
            current = self._write_manifest(
                root,
                "current.json",
                manifest(score=74, issues=7, opportunities=6),
            )
            output = root / "reports" / "comparison.json"

            exit_code = main(
                [
                    "--previous",
                    str(previous),
                    "--current",
                    str(current),
                    "--output",
                    str(output),
                ]
            )
            payload = json.loads(output.read_text(encoding="utf-8"))

        self.assertEqual(exit_code, 0)
        self.assertEqual(payload["status"], "success")
        self.assertEqual(payload["metrics"]["average_score"]["change"], 4.0)

    def test_fail_on_regression_returns_distinct_exit_code_after_writing_report(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            previous = self._write_manifest(root, "previous.json", manifest(score=80, issues=5))
            current = self._write_manifest(root, "current.json", manifest(score=77, issues=9))
            output = root / "comparison.json"

            exit_code = main(
                [
                    "--previous",
                    str(previous),
                    "--current",
                    str(current),
                    "--output",
                    str(output),
                    "--fail-on-regression",
                ]
            )
            payload = json.loads(output.read_text(encoding="utf-8"))

        self.assertEqual(exit_code, REGRESSION_EXIT_CODE)
        self.assertEqual(payload["status"], "regression")
        self.assertEqual(
            payload["regressions"],
            ["average_score_decreased", "issue_count_increased"],
        )

    def test_tolerances_prevent_false_regression_failure(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            previous = self._write_manifest(root, "previous.json", manifest(score=80, issues=5))
            current = self._write_manifest(root, "current.json", manifest(score=79.5, issues=6))
            output = root / "comparison.json"

            exit_code = main(
                [
                    "--previous",
                    str(previous),
                    "--current",
                    str(current),
                    "--output",
                    str(output),
                    "--minimum-score-change",
                    "1",
                    "--maximum-issue-increase",
                    "2",
                    "--fail-on-regression",
                ]
            )

        self.assertEqual(exit_code, 0)

    def test_invalid_manifest_returns_controlled_error(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            previous = self._write_manifest(root, "previous.json", manifest())
            current = root / "current.json"
            current.write_text("not-json", encoding="utf-8")

            exit_code = main(
                [
                    "--previous",
                    str(previous),
                    "--current",
                    str(current),
                    "--output",
                    str(root / "comparison.json"),
                ]
            )

        self.assertEqual(exit_code, 2)


if __name__ == "__main__":
    unittest.main()
