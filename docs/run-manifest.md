# SEO çalışma manifesti

`seo-opportunities` komutu `--manifest-output` verildiğinde rapor paketi başarıyla tamamlandıktan sonra makinece okunabilir bir JSON özeti üretir.

```bash
seo-opportunities \
  --catalog ikas-products.csv \
  --platform ikas \
  --search-console search-console.csv \
  --output reports/search-opportunities.csv \
  --audit-output reports/catalog-audit.csv \
  --manifest-output reports/run-manifest.json
```

Örnek çıktı:

```json
{
  "generated_at": "2026-07-28T12:00:00Z",
  "inputs": {
    "catalog": "ikas-products.csv",
    "platform": "ikas",
    "search_console": "search-console.csv"
  },
  "metrics": {
    "average_score": 63.4,
    "issue_count": 142,
    "product_count": 250,
    "traffic_opportunity_count": 38
  },
  "outputs": {
    "catalog_audit": "reports/catalog-audit.csv",
    "search_opportunities": "reports/search-opportunities.csv"
  },
  "schema_version": 1,
  "status": "success"
}
```

## Sözleşme

- `schema_version`: Tüketicilerin manifest biçimini güvenli şekilde sürümlemesini sağlar.
- `status`: Manifest yalnızca bütün istenen raporlar başarıyla yazıldıktan sonra üretildiği için şu an `success` değeridir.
- `generated_at`: UTC ve ISO 8601 biçimindedir.
- `inputs`: Kullanılan katalog, platform ve Search Console dosyasını kaydeder.
- `metrics`: Ürün, sorun, ortalama puan ve trafik fırsatı sayılarını verir.
- `outputs`: Gerçekten üretilen raporları anahtar-dosya yolu olarak listeler.

Manifest, panel veya zamanlanmış işlem gibi sonraki sistemlerin CSV içeriklerini tek tek açmadan çalışmanın sonucunu doğrulamasına yarar. Ürün adı, slug veya katalog içeriğinde değişiklik yapmaz.
