import csv
import tempfile
import unittest
from pathlib import Path

from turkmopet_seo.audit import ProductRecord
from turkmopet_seo.catalog import audit_catalog
from turkmopet_seo.search_console import (
    SearchConsoleImportError,
    SearchConsoleRow,
    prioritize_search_opportunities,
    read_search_console_csv,
    write_search_opportunities_csv,
)


class SearchConsoleTests(unittest.TestCase):
    def test_reads_turkish_export_and_percent_ctr(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "search.csv"
            source.write_text(
                "Sorgu,Sayfa,Tıklamalar,Gösterimler,TO,Konum\n"
                "jupiter cam,https://turkmopet.com/products/jupiter-cam,12,300,%4,8.5\n",
                encoding="utf-8-sig",
            )
            rows = read_search_console_csv(source)
            self.assertEqual(len(rows), 1)
            self.assertEqual(rows[0].clicks, 12)
            self.assertEqual(rows[0].impressions, 300)
            self.assertEqual(rows[0].ctr, 0.04)

    def test_rejects_missing_columns(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "search.csv"
            source.write_text("query,page\nfoo,/foo\n", encoding="utf-8")
            with self.assertRaises(SearchConsoleImportError):
                read_search_console_csv(source)

    def test_matches_page_slug_and_ranks_real_demand(self) -> None:
        report = audit_catalog(
            (
                ProductRecord(
                    name="Jupiter Cam",
                    slug="jupiter-cam",
                    meta_title="Kısa",
                    meta_description="Kısa",
                    description="Kısa",
                ),
                ProductRecord(
                    name="PCX Cam",
                    slug="pcx-cam",
                    meta_title="PCX Cam için yeterince uzun meta başlık örneği",
                    meta_description="PCX Cam için marka ve ürün detaylarını açıklayan yeterince uzun bir meta açıklama metni burada yer alır.",
                    description="PCX Cam ürününün kullanım alanı, temel özellikleri, montaj kontrolü ve bakım bilgileri hakkında yeterince ayrıntılı ürün açıklaması burada yer almaktadır. Bu metin denetim sınırını güvenli biçimde aşar.",
                ),
            )
        )
        rows = (
            SearchConsoleRow("jupiter cam", "https://turkmopet.com/products/jupiter-cam?x=1", 10, 500, 0.02, 8),
            SearchConsoleRow("jupiter 125 cam", "https://turkmopet.com/products/jupiter-cam/", 5, 200, 0.025, 10),
            SearchConsoleRow("pcx cam", "https://turkmopet.com/products/pcx-cam", 20, 100, 0.20, 2),
        )
        opportunities = prioritize_search_opportunities(report, rows)
        self.assertEqual([item.slug for item in opportunities], ["jupiter-cam", "pcx-cam"])
        self.assertEqual(opportunities[0].query_count, 2)
        self.assertEqual(opportunities[0].top_query, "jupiter cam")
        self.assertEqual(opportunities[0].impressions, 700)

    def test_ignores_unmatched_and_zero_impression_rows(self) -> None:
        report = audit_catalog((ProductRecord(name="A", slug="a"),))
        rows = (
            SearchConsoleRow("a", "https://turkmopet.com/products/a", 0, 0, 0, 9),
            SearchConsoleRow("b", "https://turkmopet.com/products/b", 1, 10, 0.1, 7),
        )
        self.assertEqual(prioritize_search_opportunities(report, rows), ())

    def test_writes_excel_compatible_opportunity_csv(self) -> None:
        report = audit_catalog((ProductRecord(name="A", slug="a"),))
        opportunities = prioritize_search_opportunities(
            report,
            (SearchConsoleRow("a sorgusu", "https://turkmopet.com/a", 2, 100, 0.02, 7),),
        )
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "reports" / "opportunities.csv"
            write_search_opportunities_csv(opportunities, output)
            with output.open(encoding="utf-8-sig", newline="") as handle:
                rows = list(csv.DictReader(handle))
            self.assertEqual(rows[0]["slug"], "a")
            self.assertEqual(rows[0]["top_query"], "a sorgusu")
            self.assertIn("opportunity_score", rows[0])


if __name__ == "__main__":
    unittest.main()
