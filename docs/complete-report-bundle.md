# Tek komutla SEO rapor paketi

`seo-opportunities` komutu katalog denetimini ve Search Console fırsat analizini tek çalışmada yürütür. Sürüm 0.3.0 ile aynı katalog okumasından isteğe bağlı dört operasyon raporu daha üretilebilir.

## Tam kullanım

```bash
seo-opportunities \
  --catalog ikas-products.csv \
  --platform ikas \
  --search-console search-console.csv \
  --output reports/search-opportunities.csv \
  --audit-output reports/catalog-audit.csv \
  --suggestions-output reports/seo-suggestions.csv \
  --group-summary-output reports/group-summary.csv \
  --priority-output reports/priority-products.csv \
  --priority-limit 50
```

Yalnızca `--catalog`, `--platform`, `--search-console` ve `--output` zorunludur. Diğer çıktılar gerektiğinde bağımsız biçimde açılabilir.

## Üretilen raporlar

- `--output`: Search Console gösterim, tıklama ve SEO kalite açığını birleştiren trafik fırsatları.
- `--audit-output`: Ürün ve alan bazında hata kodları, önem seviyesi ve kalite puanı.
- `--suggestions-output`: Meta başlık, meta açıklama ve ürün açıklaması için insan onaylı öneriler.
- `--group-summary-output`: Marka ve kategori bazında ürün, başarısız ürün, sorun ve ortalama puan özeti.
- `--priority-output`: Önce düzeltilmesi gereken sorunlu ürün kuyruğu.

`--priority-limit` yalnızca öncelikli ürün raporundaki azami satır sayısını belirler. Varsayılan değer `50`'dir ve negatif değer kabul edilmez.

## Güvenlik davranışı

- Ürün adı ve slug yalnızca okunur; değiştirilmez.
- Öneri raporundaki bütün satırlar `auto_apply_safe=False` olarak işaretlenir.
- Çıktı klasörleri gerektiğinde otomatik oluşturulur.
- CSV dosyaları Excel uyumlu UTF-8 BOM ile yazılır.
- Geçersiz katalog veya Search Console şeması kontrollü hata ve `2` çıkış kodu üretir.

## Önerilen operasyon sırası

1. `priority-products.csv` ile en kötü ürünleri belirle.
2. `search-opportunities.csv` ile gerçek trafik potansiyelini kontrol et.
3. `seo-suggestions.csv` içindeki önerileri insan gözüyle doğrula.
4. Onaylanan değişiklikleri platforma ayrı ve kontrollü bir güncelleme süreciyle uygula.
5. Sonraki Search Console dışa aktarımında CTR ve pozisyon değişimini karşılaştır.
