import tempfile
import unittest
from pathlib import Path

from turkmopet_seo import CatalogImportError, read_platform_catalog_csv


class PlatformAdapterTests(unittest.TestCase):
    def test_reads_shopify_export_with_product_category(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "shopify.csv"
            path.write_text(
                "Handle,Title,Body (HTML),Vendor,Product Category,Type,SEO Title,SEO Description\n"
                "tvs-jupiter-cam,TVS Jupiter Cam,<p>Uzun cam açıklaması</p>,TVS,Vehicle Parts > Windscreens,Cam,"
                "TVS Jupiter Cam | Türkmopet,TVS Jupiter için uzun ön cam teknik bilgileri\n",
                encoding="utf-8-sig",
            )

            products = read_platform_catalog_csv(path, "shopify")

        self.assertEqual(1, len(products))
        self.assertEqual("TVS Jupiter Cam", products[0].name)
        self.assertEqual("tvs-jupiter-cam", products[0].slug)
        self.assertEqual("TVS", products[0].brand)
        self.assertEqual("Vehicle Parts > Windscreens", products[0].category)

    def test_shopify_falls_back_to_type_when_product_category_is_absent(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "shopify.csv"
            path.write_text(
                "Handle,Title,Body (HTML),Vendor,Type,SEO Title,SEO Description\n"
                "dio-gaz-teli,Honda Dio Gaz Teli,Açıklama,Honda,Gaz Teli,Meta,Meta açıklama\n",
                encoding="utf-8",
            )

            products = read_platform_catalog_csv(path, "SHOPIFY")

        self.assertEqual("Gaz Teli", products[0].category)

    def test_reads_ikas_export_with_turkish_headers(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "ikas.csv"
            path.write_text(
                "Ürün Adı,Seo URL,Meta Başlık,Meta Açıklama,Açıklama,Marka,Kategori\n"
                "Honda PCX Ön Cam,honda-pcx-on-cam,Honda PCX Ön Cam,"
                "Honda PCX için ön cam açıklaması,Detaylı ürün açıklaması,Honda,Cam\n",
                encoding="utf-8-sig",
            )

            products = read_platform_catalog_csv(path, "ikas")

        self.assertEqual("Honda PCX Ön Cam", products[0].name)
        self.assertEqual("honda-pcx-on-cam", products[0].slug)
        self.assertEqual("Honda", products[0].brand)

    def test_missing_platform_columns_raise_clear_error(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "shopify.csv"
            path.write_text("Handle,Title\nurun,Ürün\n", encoding="utf-8")

            with self.assertRaisesRegex(CatalogImportError, "eşlenemeyen alanlar"):
                read_platform_catalog_csv(path, "shopify")

    def test_unknown_platform_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "catalog.csv"
            path.write_text("name\nÜrün\n", encoding="utf-8")

            with self.assertRaisesRegex(CatalogImportError, "Desteklenmeyen platform"):
                read_platform_catalog_csv(path, "magento")


if __name__ == "__main__":
    unittest.main()
