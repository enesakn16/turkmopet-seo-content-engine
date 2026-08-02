from __future__ import annotations

import csv
import tempfile
import unittest
from pathlib import Path

from turkmopet_seo import ProductRecord, audit_catalog
from turkmopet_seo.suggestions import (
    suggest_catalog_improvements,
    suggest_product_improvements,
    write_suggestions_csv,
)


class SuggestionTests(unittest.TestCase):
    def test_generates_review_only_suggestions_without_changing_identity(self) -> None:
        product = ProductRecord(
            name="TVS Jupiter 125 Ön Fren Balatası",
            slug="tvs-jupiter-125-on-fren-balatasi",
            meta_title="Fren balatası",
            meta_description="Kısa açıklama",
            description="Kısa ürün açıklaması",
            brand="TVS",
            category="Fren",
        )
        item = audit_catalog((product,)).items[0]

        result = suggest_product_improvements(item)

        self.assertEqual(result.name, product.name)
        self.assertEqual(result.slug, product.slug)
        self.assertEqual(
            {suggestion.field for suggestion in result.suggestions},
            {"meta_title", "meta_description", "description"},
        )
        self.assertTrue(all(not suggestion.auto_apply_safe for suggestion in result.suggestions))

    def test_title_and_meta_candidates_respect_character_limits(self) -> None:
        product = ProductRecord(
            name="Çok Uzun Ürün Adı " * 8,
            slug="uzun-urun",
            brand="Türkmopet",
            category="Motosiklet Yedek Parça ve Aksesuar",
        )
        item = audit_catalog((product,)).items[0]

        result = suggest_product_improvements(item)
        suggestions = {suggestion.field: suggestion for suggestion in result.suggestions}

        self.assertLessEqual(len(suggestions["meta_title"].suggested_value), 60)
        self.assertLessEqual(len(suggestions["meta_description"].suggested_value), 160)
        self.assertIn(product.name.split()[0], suggestions["meta_title"].suggested_value)

    def test_skips_clean_products(self) -> None:
        product = ProductRecord(
            name="TVS Jupiter 125 Ön Fren Balatası",
            slug="tvs-jupiter-125-on-fren-balatasi",
            meta_title="TVS Jupiter 125 Ön Fren Balatası | Türkmopet",
            meta_description=(
                "TVS Jupiter 125 ön fren balatası için teknik özellikler, uyumluluk "
                "bilgileri ve kullanım detayları bu ürün sayfasında yer alır."
            ),
            description=(
                "TVS Jupiter 125 için kataloglanan fren kategorisindeki bu ürünün "
                "teknik özellikleri, uyumluluk bilgileri, montaj notları ve güvenlik "
                "uyarıları doğrulanmış ürün verilerine göre açıklanır. Kullanım öncesi "
                "motosiklet model ve yıl uyumluluğu kontrol edilmelidir."
            ),
            brand="TVS",
            category="fren",
        )

        suggestions = suggest_catalog_improvements(audit_catalog((product,)))

        self.assertEqual(suggestions, ())

    def test_writes_excel_compatible_suggestion_csv(self) -> None:
        product = ProductRecord(
            name="Honda PCX Arka Fren Balatası",
            slug="honda-pcx-arka-fren-balatasi",
            brand="Honda",
            category="Fren",
        )
        suggestions = suggest_catalog_improvements(audit_catalog((product,)))

        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "reports" / "suggestions.csv"
            write_suggestions_csv(suggestions, output)

            with output.open(encoding="utf-8-sig", newline="") as handle:
                rows = list(csv.DictReader(handle))

        self.assertEqual(len(rows), 3)
        self.assertEqual(rows[0]["name"], product.name)
        self.assertEqual(rows[0]["slug"], product.slug)
        self.assertEqual(rows[0]["auto_apply_safe"], "False")


if __name__ == "__main__":
    unittest.main()
