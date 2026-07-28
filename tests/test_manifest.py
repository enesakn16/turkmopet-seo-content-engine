from __future__ import annotations

import json
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path

from turkmopet_seo.audit import ProductRecord
from turkmopet_seo.catalog import audit_catalog
from turkmopet_seo.manifest import build_run_manifest, write_run_manifest
from turkmopet_seo.search_console import ProductSearchOpportunity


class RunManifestTests(unittest.TestCase):
    def test_builds_stable_manifest_with_metrics_and_sorted_outputs(self) -> None:
        report = audit_catalog(
            (
                ProductRecord(
                    name="TVS Jupiter 125 Ön Fren Balatası",
                    slug="tvs-jupiter-125-on-fren-balatasi",
                    meta_title="Kısa başlık",
                    meta_description="Kısa açıklama",
                    description="Kısa içerik",
                    brand="TVS",
                    category="Fren",
                ),
            )
        )
        opportunities = (
            ProductSearchOpportunity(
                row_number=2,
                name="TVS Jupiter 125 Ön Fren Balatası",
                slug="tvs-jupiter-125-on-fren-balatasi",
                audit_score=report.items[0].result.score,
                clicks=4,
                impressions=200,
                ctr=0.02,
                average_position=8.5,
                query_count=1,
                top_query="jupiter 125 fren balatası",
                opportunity_score=42.5,
            ),
        )

        manifest = build_run_manifest(
            catalog_path="ikas.csv",
            platform="ikas",
            search_console_path="search-console.csv",
            report=report,
            opportunities=opportunities,
            outputs={
                "search_opportunities": "reports/opportunities.csv",
                "catalog_audit": "reports/audit.csv",
            },
            generated_at=datetime(2026, 7, 28, 12, 0, tzinfo=timezone.utc),
        )

        self.assertEqual(manifest["schema_version"], 1)
        self.assertEqual(manifest["status"], "success")
        self.assertEqual(manifest["generated_at"], "2026-07-28T12:00:00Z")
        self.assertEqual(manifest["metrics"]["product_count"], 1)
        self.assertEqual(manifest["metrics"]["issue_count"], report.issue_count)
        self.assertEqual(manifest["metrics"]["traffic_opportunity_count"], 1)
        self.assertEqual(
            list(manifest["outputs"]),
            ["catalog_audit", "search_opportunities"],
        )

    def test_rejects_naive_generated_at(self) -> None:
        report = audit_catalog(())
        with self.assertRaisesRegex(ValueError, "saat dilimi"):
            build_run_manifest(
                catalog_path="catalog.csv",
                platform="standard",
                search_console_path="search-console.csv",
                report=report,
                opportunities=(),
                outputs={},
                generated_at=datetime(2026, 7, 28, 12, 0),
            )

    def test_writes_utf8_json_and_creates_parent_directory(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "nested" / "manifest.json"
            write_run_manifest({"status": "başarılı"}, output)

            self.assertEqual(
                json.loads(output.read_text(encoding="utf-8")),
                {"status": "başarılı"},
            )


if __name__ == "__main__":
    unittest.main()
