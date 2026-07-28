# SEO çalışma geçmişini karşılaştırma

`seo-compare-runs`, iki başarılı `schema_version: 1` çalışma manifestini karşılaştırır ve makinece okunabilir JSON sonuç üretir.

## Temel kullanım

```bash
seo-compare-runs \
  --previous reports/previous-manifest.json \
  --current reports/current-manifest.json \
  --output reports/comparison.json
```

Komut şu metriklerin önceki, güncel ve değişim değerlerini kaydeder:

- ortalama SEO puanı
- sorun sayısı
- ürün sayısı
- trafik fırsatı sayısı

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
- `3`: geçerli karşılaştırmada regresyon tespit edildi

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

Bu örnekte 1 puana kadar SEO puanı düşüşü ve 2 adede kadar sorun artışı regresyon sayılmaz.

## Regresyon kodları

- `average_score_decreased`: ortalama SEO puanı izin verilen toleranstan fazla düştü
- `issue_count_increased`: sorun sayısı izin verilen toleranstan fazla arttı

Trafik fırsatı ve ürün sayısı değişimleri raporlanır ancak tek başına regresyon üretmez; bu metriklerin yorumu katalog kapsamı ve Search Console dönemine bağlıdır.
