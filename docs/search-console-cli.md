# Search Console fırsat CLI'ı

`seo-opportunities`, katalog SEO denetimini Search Console sorgu verisiyle tek komutta birleştirir. Ürün adı, slug veya katalog içeriği değiştirilmez; yalnızca Excel uyumlu bir fırsat raporu üretilir.

## İkas dışa aktarımı

```bash
seo-opportunities \
  --catalog ikas-products.csv \
  --platform ikas \
  --search-console search-console.csv \
  --output reports/search-opportunities.csv
```

## Shopify dışa aktarımı

```bash
seo-opportunities \
  --catalog shopify-products.csv \
  --platform shopify \
  --search-console search-console.csv \
  --output reports/search-opportunities.csv
```

## Standart şema

Katalog daha önce standart şemaya dönüştürüldüyse `--platform standard` kullanılabilir:

```text
name,slug,meta_title,meta_description,description,brand,category
```

```bash
seo-opportunities \
  --catalog products.csv \
  --platform standard \
  --search-console search-console.csv \
  --output reports/search-opportunities.csv
```

## Çıktı

```text
row_number,name,slug,audit_score,clicks,impressions,ctr,average_position,query_count,top_query,opportunity_score
```

Komut başarılı olduğunda `0`, katalog veya Search Console biçimi geçersiz olduğunda `2` çıkış kodu döndürür. Çıktı klasörü yoksa otomatik oluşturulur.

## Güvenlik sınırları

- Ürün adı ve slug yalnızca okunur.
- Eşleşmeyen Search Console URL'leri atlanır.
- Katalog veya Search Console dosyasında eksik kolon varsa açık hata üretilir.
- Hiçbir öneri veya katalog değişikliği otomatik uygulanmaz.
