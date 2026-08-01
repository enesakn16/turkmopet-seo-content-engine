# SEO çalışma geçmişini karşılaştırma

`seo-compare-runs`, iki başarılı `schema_version: 1` çalışma manifestini karşılaştırır ve makinece okunabilir JSON sonuç üretir.

## Temel kullanım

```bash
seo-compare-runs \
  --previous reports/previous-manifest.json \
  --current reports/current-manifest.json \
  --output reports/comparison.json
```

Komut genel metriklerin önceki, güncel ve değişim değerlerini kaydeder:

- ortalama SEO puanı
- sorun sayısı
- ürün sayısı
- trafik fırsatı sayısı

Yeni manifestlerde ayrıca ortak marka ve kategoriler tek tek karşılaştırılır. Grup sonuçları en ciddi gerileme önce olacak şekilde sıralanır; böylece genel puan sabit kalsa bile örneğin yalnızca `TVS` markasındaki veya `Fren` kategorisindeki bozulma görünür.

## CI ve zamanlanmış kontroller

Regresyon olduğunda sıfır olmayan çıkış kodu almak için:

```bash
seo-compare-runs \
  --previous reports/previous-manifest.json \
  --current reports/current-manifest.json \
  --output reports/comparison.json \
  --fail-on-regression
```

Çıkış kodları:

- `0`: karşılaştırma başarılı; regresyon yok veya `--fail-on-regression` kullanılmadı
- `2`: bozuk/uyumsuz manifest ya da dosya hatası
- `3`: genel, marka veya kategori düzeyinde regresyon tespit edildi

Karşılaştırma raporu, regresyon durumunda bile çıkış kodu dönmeden önce yazılır. Böylece CI artifact veya hata incelemesi için kanıt korunur.

## Toleranslar

Küçük günlük oynaklıkları hata saymamak için:

```bash
seo-compare-runs \
  --previous reports/previous-manifest.json \
  --current reports/current-manifest.json \
  --output reports/comparison.json \
  --minimum-score-change 1.0 \
  --maximum-issue-increase 2 \
  --fail-on-regression
```

Bu toleranslar hem genel metriklere hem de marka/kategori kırılımlarına uygulanır. Örnekte 1 puana kadar SEO puanı düşüşü ve 2 adede kadar sorun artışı regresyon sayılmaz.

## Regresyon kodları

Genel kodlar:

- `average_score_decreased`
- `issue_count_increased`

Grup kodları boyut, ad ve neden içerir:

```text
brand:TVS:average_score_decreased
category:Fren:issue_count_increased
```

Yalnızca her iki manifestte de bulunan gruplar karşılaştırılır. Yeni veya kaldırılmış marka/kategoriler otomatik regresyon sayılmaz; katalog kapsamındaki değişiklik yanlış alarm üretmez.

Trafik fırsatı ve ürün sayısı değişimleri raporlanır ancak tek başına regresyon üretmez; bu metriklerin yorumu katalog kapsamı ve Search Console dönemine bağlıdır.
