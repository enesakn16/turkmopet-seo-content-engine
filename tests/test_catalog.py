import csv
import tempfile
import unittest
from pathlib import Path

from turkmopet_seo import (
    CatalogImportError,
    ProductRecord,
    audit_catalog,
    read_catalog_csv,
    write_audit_csv,
)


class CatalogPipelineTests(unittest.TestCase):
    def test_reads_excel_compatible_catalog_csv(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "products.csv"
            path.write_text(
                "name,slug,meta_title,meta_description,description,brand,category\n"
                "TVS Jupiter 125 Cam,tvs-jupiter-125-cam,TVS Jupiter 125 Cam Uzun Ön Cam,"
                "TVS Jupiter 125 için uzun ön cam ürünü ve kullanım bilgileri,"
                "TVS Jupiter 125 scooter için rüzgar koruması sağlayan cam açıklaması,TVS,Cam\n",
                encoding="utf-8-sig",
            )

            products = read_catalog_csv(path)

        self.assertEqual(1, len(products))
        self.assertEqual("TVS Jupiter 125 Cam", products[0].name)
        self.assertEqual("tvs-jupiter-125-cam", products[0].slug)

    def test_missing_columns_raise_clear_import_error(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "products.csv"
            path.write_text("name,slug\nÜrün,urun\n", encoding="utf-8")

            with self.assertRaisesRegex(CatalogImportError, "Eksik katalog kolonları"):
                read_catalog_csv(path)

    def test_duplicate_slug_and_meta_content_are_reported(self) -> None:
        shared_title = "TVS Jupiter 125 Yedek Parça ve Aksesuar"
        shared_meta = (
            "TVS Jupiter 125 için uyumlu yedek parça ve aksesuar seçeneklerini teknik bilgilerle inceleyin."
        )
        products = (
            ProductRecord(
                name="TVS Jupiter 125 Ön Cam",
                slug="tvs-jupiter-125-parca",
                meta_title=shared_title,
                meta_description=shared_meta,
                description="TVS Jupiter 125 Cam kategorisindeki ürün için detaylı teknik açıklama " * 3,
                brand="TVS",
                category="Cam",
            ),
            ProductRecord(
                name="TVS Jupiter 125 Çanta Demiri",
                slug="tvs-jupiter-125-parca",
                meta_title=shared_title,
                meta_description=shared_meta,
                description="TVS Jupiter 125 Demir kategorisindeki ürün için detaylı teknik açıklama " * 3,
                brand="TVS",
                category="Demir",
            ),
        )

        report = audit_catalog(products)
        first_codes = {issue.code for issue in report.items[0].result.issues}
        second_codes = {issue.code for issue in report.items[1].result.issues}

        for codes in (first_codes, second_codes):
            self.assertIn("slug.duplicate", codes)
            self.assertIn("meta_title.duplicate", codes)
            self.assertIn("meta_description.duplicate", codes)
        self.assertFalse(report.items[0].result.passed)
        self.assertEqual(2, report.product_count)
        self.assertGreaterEqual(report.issue_count, 6)

    def test_audit_report_is_written_as_excel_friendly_csv(self) -> None:
        report = audit_catalog((ProductRecord(name="Honda Dio Gaz Teli", slug="honda-dio-gaz-teli"),))

        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "audit.csv"
            write_audit_csv(report, output)
            with output.open("r", encoding="utf-8-sig", newline="") as handle:
                rows = list(csv.DictReader(handle))

        self.assertTrue(rows)
        self.assertEqual("Honda Dio Gaz Teli", rows[0]["name"])
        self.assertEqual("2", rows[0]["row_number"])
        self.assertIn("score", rows[0])
        self.assertIn("code", rows[0])


if __name__ == "__main__":
    unittest.main()
