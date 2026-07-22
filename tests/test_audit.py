import unittest

from turkmopet_seo import ProductRecord, Severity, audit_product


class ProductSeoAuditTests(unittest.TestCase):
    def test_complete_product_receives_full_score(self) -> None:
        product = ProductRecord(
            name="TVS Jupiter 125 Ön Fren Balatası",
            slug="tvs-jupiter-125-on-fren-balatasi",
            meta_title="TVS Jupiter 125 Ön Fren Balatası | Türkmopet",
            meta_description=(
                "TVS Jupiter 125 için uyumlu ön fren balatasını teknik özellikleri, kullanım bilgileri "
                "ve montaj notlarıyla Türkmopet güvencesiyle inceleyin."
            ),
            description=(
                "TVS Jupiter 125 scooter modellerinde ön fren sisteminde kullanılan bu fren balatası, "
                "düzenli bakım sırasında aşınan parçanın yenilenmesi için tercih edilir. Fren kategorisindeki "
                "ürünün montajı, bağlantılar kontrol edilerek uzman kişi tarafından yapılmalıdır."
            ),
            brand="TVS",
            category="Fren",
        )

        result = audit_product(product)

        self.assertEqual(100, result.score)
        self.assertTrue(result.passed)
        self.assertEqual((), result.issues)

    def test_missing_required_content_creates_errors(self) -> None:
        result = audit_product(ProductRecord(name="", slug=""))

        error_codes = {
            issue.code for issue in result.issues if issue.severity == Severity.ERROR
        }
        self.assertEqual(
            {
                "name.empty",
                "slug.empty",
                "meta_title.empty",
                "meta_description.empty",
                "description.empty",
            },
            error_codes,
        )
        self.assertFalse(result.passed)
        self.assertEqual(0, result.score)

    def test_short_fields_and_missing_context_are_reported(self) -> None:
        product = ProductRecord(
            name="Honda Dio Gaz Teli",
            slug="honda-dio-gaz-teli",
            meta_title="Gaz Teli",
            meta_description="Kısa açıklama",
            description="Kısa ürün açıklaması",
            brand="Honda",
            category="Gaz Teli",
        )

        result = audit_product(product)
        codes = {issue.code for issue in result.issues}

        self.assertIn("meta_title.short", codes)
        self.assertIn("meta_title.missing_name", codes)
        self.assertIn("meta_description.short", codes)
        self.assertIn("meta_description.missing_brand", codes)
        self.assertIn("description.short", codes)
        self.assertIn("description.missing_category", codes)

    def test_product_identity_is_never_modified(self) -> None:
        product = ProductRecord(
            name="Yamaha Crypton C8 Sele Altı Takımı Siyah",
            slug="yamaha-crypton-c8-sele-alti-takimi-siyah",
        )

        audit_product(product)

        self.assertEqual("Yamaha Crypton C8 Sele Altı Takımı Siyah", product.name)
        self.assertEqual("yamaha-crypton-c8-sele-alti-takimi-siyah", product.slug)


if __name__ == "__main__":
    unittest.main()
