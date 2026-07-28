from __future__ import annotations

import csv
import tempfile
import unittest
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path

from turkmopet_seo.cli import main


class SeoReportBundleCliTests(unittest.TestCase):
    def test_exports_complete_report_bundle_in_one_run(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            catalog = root / "ikas.csv"
            search_console = root / "search-console.csv"
            reports = root / "reports"
            outputs = {
                "opportunities": reports / "opportunities.csv",
                "audit": reports / "audit.csv",
                "suggestions": reports / "suggestions.csv",
                "groups": reports / "groups.csv",
                "priorities": reports / "priorities.csv",
            }

            catalog.write_text(
                "name,slug,metaTitle,metaDescription,description,brand,category\n"
                "TVS Jupiter 125 Ön Fren Balatası,tvs-jupiter-125-on-fren-balatasi,"
                "Kısa,Kısa,Kısa,TVS,Fren\n"
                "Mondial Revival Egzoz,mondial-revival-egzoz,"
                "Kısa,Kısa,Kısa,Mondial,Egzoz\n",
                encoding="utf-8-sig",
            )
            search_console.write_text(
                "query,page,clicks,impressions,ctr,position\n"
                "jupiter fren,https://turkmopet.com/tvs-jupiter-125-on-fren-balatasi,2,100,0.02,7\n"
                "revival egzoz,https://turkmopet.com/mondial-revival-egzoz,1,80,0.0125,9\n",
                encoding="utf-8-sig",
            )

            stdout = StringIO()
            with redirect_stdout(stdout):
                exit_code = main(
                    [
                        "--catalog", str(catalog),
                        "--platform", "ikas",
                        "--search-console", str(search_console),
                        "--output", str(outputs["opportunities"]),
                        "--audit-output", str(outputs["audit"]),
                        "--suggestions-output", str(outputs["suggestions"]),
                        "--group-summary-output", str(outputs["groups"]),
                        "--priority-output", str(outputs["priorities"]),
                        "--priority-limit", "1",
                    ]
                )

            self.assertEqual(exit_code, 0)
            for output in outputs.values():
                self.assertTrue(output.exists(), output)

            with outputs["priorities"].open(encoding="utf-8-sig", newline="") as handle:
                self.assertEqual(len(list(csv.DictReader(handle))), 1)

            with outputs["suggestions"].open(encoding="utf-8-sig", newline="") as handle:
                suggestions = list(csv.DictReader(handle))
            self.assertTrue(suggestions)
            self.assertTrue(all(row["auto_apply_safe"] == "False" for row in suggestions))

            with outputs["groups"].open(encoding="utf-8-sig", newline="") as handle:
                groups = list(csv.DictReader(handle))
            self.assertEqual({row["dimension"] for row in groups}, {"brand", "category"})

            text = stdout.getvalue()
            for label in ("denetim:", "öneri:", "grup özeti:", "öncelik:"):
                self.assertIn(label, text)


if __name__ == "__main__":
    unittest.main()
