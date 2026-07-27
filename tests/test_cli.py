from __future__ import annotations

import csv
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from io import StringIO
from pathlib import Path

from turkmopet_seo.cli import main


class SeoOpportunitiesCliTests(unittest.TestCase):
    def test_generates_search_opportunity_report_from_ikas_export(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            catalog = root / "ikas.csv"
            search_console = root / "search-console.csv"
            output = root / "reports" / "opportunities.csv"

            catalog.write_text(
                "name,slug,metaTitle,metaDescription,description,brand,category\n"
                "TVS Jupiter 125 Ön Fren Balatası,tvs-jupiter-125-on-fren-balatasi,"
                "Kısa başlık,Kısa açıklama,Kısa içerik,TVS,Fren\n",
                encoding="utf-8-sig",
            )
            search_console.write_text(
                "Sorgu,Sayfa,Tıklamalar,Gösterimler,TO,Konum\n"
                "jupiter 125 fren balatası,https://turkmopet.com/tvs-jupiter-125-on-fren-balatasi,4,200,2%,8.5\n",
                encoding="utf-8-sig",
            )

            stdout = StringIO()
            with redirect_stdout(stdout):
                exit_code = main(
                    [
                        "--catalog",
                        str(catalog),
                        "--platform",
                        "ikas",
                        "--search-console",
                        str(search_console),
                        "--output",
                        str(output),
                    ]
                )

            self.assertEqual(exit_code, 0)
            self.assertTrue(output.exists())
            with output.open(encoding="utf-8-sig", newline="") as handle:
                rows = list(csv.DictReader(handle))
            self.assertEqual(len(rows), 1)
            self.assertEqual(rows[0]["slug"], "tvs-jupiter-125-on-fren-balatasi")
            self.assertEqual(rows[0]["impressions"], "200")
            self.assertIn("1 trafik fırsatı", stdout.getvalue())

    def test_supports_standard_catalog_schema(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            catalog = root / "catalog.csv"
            search_console = root / "search-console.csv"
            output = root / "opportunities.csv"

            catalog.write_text(
                "name,slug,meta_title,meta_description,description,brand,category\n"
                "Ürün,urun,Ürün başlığı,Ürün açıklaması,Detaylı ürün açıklaması,Marka,Kategori\n",
                encoding="utf-8",
            )
            search_console.write_text(
                "query,page,clicks,impressions,ctr,position\n"
                "ürün,https://turkmopet.com/urun,1,10,0.1,4\n",
                encoding="utf-8",
            )

            exit_code = main(
                [
                    "--catalog",
                    str(catalog),
                    "--platform",
                    "standard",
                    "--search-console",
                    str(search_console),
                    "--output",
                    str(output),
                ]
            )

            self.assertEqual(exit_code, 0)
            self.assertTrue(output.exists())

    def test_returns_controlled_error_for_invalid_search_console_file(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            catalog = root / "catalog.csv"
            search_console = root / "search-console.csv"
            output = root / "opportunities.csv"

            catalog.write_text(
                "name,slug,meta_title,meta_description,description,brand,category\n"
                "Ürün,urun,Başlık,Açıklama,İçerik,Marka,Kategori\n",
                encoding="utf-8",
            )
            search_console.write_text("query,page\nürün,https://turkmopet.com/urun\n", encoding="utf-8")

            stderr = StringIO()
            with redirect_stderr(stderr):
                exit_code = main(
                    [
                        "--catalog",
                        str(catalog),
                        "--platform",
                        "standard",
                        "--search-console",
                        str(search_console),
                        "--output",
                        str(output),
                    ]
                )

            self.assertEqual(exit_code, 2)
            self.assertFalse(output.exists())
            self.assertIn("Eksik Search Console kolonları", stderr.getvalue())


if __name__ == "__main__":
    unittest.main()
