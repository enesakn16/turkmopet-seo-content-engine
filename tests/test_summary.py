import csv
import tempfile
import unittest
from pathlib import Path

from turkmopet_seo import (
    AuditIssue,
    AuditResult,
    CatalogAuditItem,
    CatalogAuditReport,
    ProductRecord,
    Severity,
    summarize_catalog,
    write_group_summary_csv,
    write_priority_csv,
)


class CatalogSummaryTests(unittest.TestCase):
    def setUp(self) -> None:
        self.report = CatalogAuditReport(
            items=(
                self._item(
                    2,
                    "TVS Jupiter Cam",
                    "tvs-jupiter-cam",
                    "TVS",
                    "Cam",
                    35,
                    AuditIssue("meta_title.empty", Severity.ERROR, "meta_title", "Eksik"),
                    AuditIssue("description.short", Severity.WARNING, "description", "Kısa"),
                ),
                self._item(
                    3,
                    "TVS Jupiter Paspas",
                    "tvs-jupiter-paspas",
                    "TVS",
                    "Paspas",
                    70,
                    AuditIssue("meta_description.short", Severity.WARNING, "meta_description", "Kısa"),
                ),
                self._item(
                    4,
                    "Honda Dio Gaz Teli",
                    "honda-dio-gaz-teli",
                    "Honda",
                    "Tel",
                    90,
                ),
            )
        )

    def test_groups_are_sorted_by_lowest_average_score(self) -> None:
        summary = summarize_catalog(self.report)

        self.assertEqual([item.name for item in summary.brands], ["TVS", "Honda"])
        self.assertEqual(summary.brands[0].product_count, 2)
        self.assertEqual(summary.brands[0].failed_count, 1)
        self.assertEqual(summary.brands[0].issue_count, 3)
        self.assertEqual(summary.brands[0].average_score, 52.5)
        self.assertEqual(summary.categories[0].name, "Cam")

    def test_priorities_put_low_score_and_error_first(self) -> None:
        summary = summarize_catalog(self.report, priority_limit=1)

        self.assertEqual(len(summary.priorities), 1)
        self.assertEqual(summary.priorities[0].slug, "tvs-jupiter-cam")
        self.assertEqual(summary.priorities[0].highest_severity, "error")
        self.assertEqual(summary.issue_codes[0], ("description.short", 1))

    def test_rejects_negative_priority_limit(self) -> None:
        with self.assertRaisesRegex(ValueError, "sıfırdan küçük"):
            summarize_catalog(self.report, priority_limit=-1)

    def test_writes_excel_friendly_group_and_priority_reports(self) -> None:
        summary = summarize_catalog(self.report)
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            groups_path = root / "groups.csv"
            priorities_path = root / "priorities.csv"
            write_group_summary_csv(summary, groups_path)
            write_priority_csv(summary, priorities_path)

            with groups_path.open(encoding="utf-8-sig", newline="") as handle:
                groups = list(csv.DictReader(handle))
            with priorities_path.open(encoding="utf-8-sig", newline="") as handle:
                priorities = list(csv.DictReader(handle))

        self.assertEqual(groups[0]["dimension"], "brand")
        self.assertEqual(groups[0]["name"], "TVS")
        self.assertEqual(priorities[0]["slug"], "tvs-jupiter-cam")
        self.assertEqual(priorities[0]["highest_severity"], "error")

    @staticmethod
    def _item(
        row_number: int,
        name: str,
        slug: str,
        brand: str,
        category: str,
        score: int,
        *issues: AuditIssue,
    ) -> CatalogAuditItem:
        return CatalogAuditItem(
            row_number=row_number,
            product=ProductRecord(
                name=name,
                slug=slug,
                brand=brand,
                category=category,
            ),
            result=AuditResult(score=score, issues=tuple(issues)),
        )


if __name__ == "__main__":
    unittest.main()
