import csv
import tempfile
import unittest
from pathlib import Path

from turkmopet_seo.cannibalization import detect_cannibalization, write_cannibalization_csv
from turkmopet_seo.cannibalization_cli import main
from turkmopet_seo.search_console import SearchConsoleRow


class CannibalizationTests(unittest.TestCase):
    def test_detects_and_prioritizes_split_query_demand(self) -> None:
        rows = (
            SearchConsoleRow("jupiter cam", "https://turkmopet.com/a", 8, 120, 0.066, 7),
            SearchConsoleRow(" Jupiter   Cam ", "https://turkmopet.com/b/", 6, 100, 0.06, 9),
            SearchConsoleRow("pcx cam", "https://turkmopet.com/pcx", 20, 200, 0.1, 4),
        )
        conflicts = detect_cannibalization(rows)
        self.assertEqual(len(conflicts), 1)
        conflict = conflicts[0]
        self.assertEqual(conflict.query, "jupiter cam")
        self.assertEqual(conflict.page_count, 2)
        self.assertEqual(conflict.total_impressions, 220)
        self.assertEqual(conflict.severity, "critical")
        self.assertEqual(conflict.action_type, "consolidate_or_canonical_review")
        self.assertEqual([page.slug for page in conflict.pages], ["a", "b"])

    def test_recommends_intent_separation_for_warning_conflict(self) -> None:
        rows = (
            SearchConsoleRow("pcx siperlik", "/lider", 20, 650, 0.03, 5),
            SearchConsoleRow("pcx siperlik", "/ikincil", 8, 350, 0.02, 9),
        )
        conflict = detect_cannibalization(rows)[0]
        self.assertEqual(conflict.severity, "warning")
        self.assertEqual(conflict.action_type, "separate_search_intent")
        self.assertIn("arama niyetlerine", conflict.recommended_action)

    def test_marks_dominant_page_and_strengthens_leader(self) -> None:
        rows = (
            SearchConsoleRow("yağ filtresi", "/ana", 30, 900, 0.03, 3),
            SearchConsoleRow("yağ filtresi", "/ikincil", 1, 100, 0.01, 16),
        )
        conflict = detect_cannibalization(rows)[0]
        self.assertEqual(conflict.severity, "review")
        self.assertEqual(conflict.leading_share, 0.9)
        self.assertEqual(conflict.action_type, "strengthen_leading_page")
        self.assertIn("/ana", conflict.recommended_action)

    def test_three_pages_trigger_consolidation_review(self) -> None:
        rows = (
            SearchConsoleRow("cub egzoz", "/a", 10, 700, 0.01, 5),
            SearchConsoleRow("cub egzoz", "/b", 2, 100, 0.02, 10),
            SearchConsoleRow("cub egzoz", "/c", 1, 100, 0.01, 15),
        )
        conflict = detect_cannibalization(rows)[0]
        self.assertEqual(conflict.severity, "warning")
        self.assertEqual(conflict.action_type, "consolidate_or_canonical_review")

    def test_filters_low_signal_pages_before_classification(self) -> None:
        rows = (
            SearchConsoleRow("pcx cam", "/ana", 12, 95, 0.126, 4),
            SearchConsoleRow("pcx cam", "/noise", 0, 5, 0.0, 47),
        )
        self.assertEqual(detect_cannibalization(rows), ())

        conflicts = detect_cannibalization(rows, minimum_page_impressions=5)
        self.assertEqual(len(conflicts), 1)
        self.assertEqual(conflicts[0].page_count, 2)
        self.assertEqual(conflicts[0].total_impressions, 100)

    def test_aggregates_rows_before_applying_page_threshold(self) -> None:
        rows = (
            SearchConsoleRow("kask camı", "/a", 3, 40, 0.075, 5),
            SearchConsoleRow("kask camı", "/b", 0, 6, 0.0, 12),
            SearchConsoleRow("kask camı", "/b", 1, 5, 0.2, 11),
        )
        conflict = detect_cannibalization(rows)[0]
        self.assertEqual(conflict.page_count, 2)
        self.assertEqual(conflict.total_impressions, 51)

    def test_respects_thresholds_and_rejects_invalid_config(self) -> None:
        rows = (
            SearchConsoleRow("a", "/a", 1, 20, 0.05, 5),
            SearchConsoleRow("a", "/b", 1, 20, 0.05, 6),
        )
        self.assertEqual(detect_cannibalization(rows), ())
        with self.assertRaises(ValueError):
            detect_cannibalization(rows, minimum_pages=1)
        with self.assertRaises(ValueError):
            detect_cannibalization(rows, minimum_page_impressions=0)
        with self.assertRaises(ValueError):
            detect_cannibalization(
                rows,
                minimum_impressions=20,
                minimum_page_impressions=21,
            )

    def test_writes_excel_compatible_csv_with_action_fields(self) -> None:
        conflicts = detect_cannibalization((
            SearchConsoleRow("a", "/a", 2, 80, 0.025, 5),
            SearchConsoleRow("a", "/b", 1, 70, 0.014, 8),
        ))
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "report.csv"
            write_cannibalization_csv(conflicts, output)
            self.assertTrue(output.read_bytes().startswith(b"\xef\xbb\xbf"))
            with output.open(encoding="utf-8-sig", newline="") as handle:
                rows = list(csv.DictReader(handle))
            self.assertEqual(len(rows), 2)
            self.assertEqual(rows[0]["severity"], "critical")
            self.assertEqual(rows[0]["action_type"], "consolidate_or_canonical_review")
            self.assertTrue(rows[0]["recommended_action"])

    def test_cli_returns_warning_code_when_conflicts_exist(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "search.csv"
            output = Path(directory) / "report.csv"
            source.write_text(
                "query,page,clicks,impressions,ctr,position\n"
                "jupiter cam,https://turkmopet.com/a,4,80,5%,7\n"
                "jupiter cam,https://turkmopet.com/b,3,70,4%,9\n",
                encoding="utf-8-sig",
            )
            self.assertEqual(main(["--input", str(source), "--output", str(output)]), 1)
            self.assertTrue(output.exists())

    def test_cli_accepts_custom_page_signal_threshold(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "search.csv"
            output = Path(directory) / "report.csv"
            source.write_text(
                "query,page,clicks,impressions,ctr,position\n"
                "pcx cam,https://turkmopet.com/a,4,45,8%,7\n"
                "pcx cam,https://turkmopet.com/b,1,5,20%,9\n",
                encoding="utf-8-sig",
            )
            self.assertEqual(main(["--input", str(source), "--output", str(output)]), 0)
            self.assertEqual(
                main([
                    "--input", str(source),
                    "--output", str(output),
                    "--minimum-page-impressions", "5",
                ]),
                1,
            )


if __name__ == "__main__":
    unittest.main()
