# Türkmopet SEO Content Engine

Motosiklet yedek parça kataloglarında ürün adı ve slug alanlarına dokunmadan SEO içerik kalitesini analiz eden Python araç seti.

## Katalog SEO denetçisi

`audit_product` tek ürünü, `audit_catalog` ise bütün kataloğu analiz eder. Hiçbir akış ürün adı veya slug üzerinde değişiklik yapmaz. Böylece mevcut URL'ler, pazaryeri eşleşmeleri ve katalog kimliği korunur.

Kontrol edilen alanlar:

- ürün adı ve slug zorunluluğu
- meta başlık uzunluğu
- meta açıklama uzunluğu
- ürün açıklaması yeterliliği
- meta başlıkta ürün adı bağlamı
- meta açıklamada marka bağlamı
- açıklamada kategori bağlamı
- katalog içindeki mükerrer slug değerleri
- tekrar eden meta başlıklar
- tekrar eden meta açıklamalar

Sonuç olarak ürün bazında 0–100 kalite puanı ve alan bazlı hata listesi döner.

## Kurulum

```bash
python -m pip install -e .
```

## Tek ürün kullanımı

```python
from turkmopet_seo import ProductRecord, audit_product

product = ProductRecord(
    name="TVS Jupiter 125 Ön Fren Balatası",
    slug="tvs-jupiter-125-on-fren-balatasi",
    meta_title="TVS Jupiter 125 Ön Fren Balatası | Türkmopet",
    meta_description="TVS Jupiter 125 için uyumlu ön fren balatasını teknik özellikleri ve kullanım bilgileriyle inceleyin.",
    description="Ürün açıklaması burada yer alır.",
    brand="TVS",
    category="Fren",
)

result = audit_product(product)
print(result.score)
for issue in result.issues:
    print(issue.severity, issue.field, issue.message)
```

## CSV katalog analizi

Standart girdi dosyası UTF-8 veya Excel uyumlu UTF-8 BOM olabilir ve şu kolonları içermelidir:

```text
name,slug,meta_title,meta_description,description,brand,category
```

```python
from turkmopet_seo import audit_catalog, read_catalog_csv, write_audit_csv

products = read_catalog_csv("products.csv")
report = audit_catalog(products)
write_audit_csv(report, "reports/seo-audit.csv")

print(report.product_count)
print(report.issue_count)
print(report.average_score)
```

Çıktı CSV'si Excel ile açılabilir ve her sorun için şu bilgileri verir:

```text
row_number,name,slug,score,passed,severity,field,code,message
```

Mükerrer slug bir `error`, tekrar eden meta başlık ve meta açıklamalar ise `warning` olarak raporlanır. Ürün adı ve slug yalnızca okunur; hiçbir zaman yeniden yazılmaz.

## Marka, kategori ve öncelik raporları

Binlerce ürün içeren kataloglarda tek tek hata okumak yerine önce en problemli marka, kategori ve ürünleri görmek için `summarize_catalog` kullanılır:

```python
from turkmopet_seo import (
    summarize_catalog,
    write_group_summary_csv,
    write_priority_csv,
)

summary = summarize_catalog(report, priority_limit=50)
write_group_summary_csv(summary, "reports/group-summary.csv")
write_priority_csv(summary, "reports/priority-products.csv")
```

Grup raporu marka ve kategorileri en düşük ortalama puandan başlayarak sıralar:

```text
dimension,name,product_count,failed_count,issue_count,average_score
```

Öncelik raporu yalnızca sorunlu ürünleri düşük puan, en yüksek önem seviyesi ve sorun sayısına göre deterministik biçimde sıralar:

```text
row_number,name,slug,brand,category,score,issue_count,highest_severity
```

`summary.issue_codes`, katalogdaki hata kodlarının toplam dağılımını en sık sorundan başlayarak verir. Boş marka veya kategori değerleri `(belirtilmemiş)` grubunda toplanır.

## Shopify ve İkas adaptörleri

Ham platform dışa aktarımlarını elle kolon düzenlemeden standart `ProductRecord` şemasına çevirmek için `read_platform_catalog_csv` kullanılır:

```python
from turkmopet_seo import audit_catalog, read_platform_catalog_csv, write_audit_csv

products = read_platform_catalog_csv("shopify-products.csv", "shopify")
report = audit_catalog(products)
write_audit_csv(report, "reports/shopify-seo-audit.csv")
```

İkas için:

```python
products = read_platform_catalog_csv("ikas-products.csv", "ikas")
```

Shopify eşleştirmeleri:

- `Title` → ürün adı
- `Handle` → slug
- `SEO Title` / `SEO Description` → meta alanları
- `Body (HTML)` → ürün açıklaması
- `Vendor` → marka
- `Product Category`, yoksa `Type` → kategori

İkas adaptörü İngilizce teknik kolon adlarının yanında `Ürün Adı`, `Seo URL`, `Meta Başlık`, `Meta Açıklama`, `Açıklama`, `Marka` ve `Kategori` gibi Türkçe başlıkları da tanır. Zorunlu bir alan eşlenemezse sessizce boş veri üretmek yerine açık `CatalogImportError` verir.

## Test

```bash
python -m unittest discover -s tests -v
python -m compileall -q src tests
```

CI, pull request ve `main` pushlarında Python 3.11, 3.12 ve 3.13 üzerinde çalışır.

## Mimari

```text
Shopify / İkas / standart CSV
        ↓
read_platform_catalog_csv / read_catalog_csv
        ↓
ProductRecord[]
        ↓
audit_catalog
        ├── audit_product
        ├── mükerrer slug tespiti
        ├── tekrar eden meta başlık tespiti
        └── tekrar eden meta açıklama tespiti
        ↓
CatalogAuditReport
        ├── write_audit_csv
        └── summarize_catalog
                ├── marka ve kategori özetleri
                ├── hata kodu dağılımı
                └── öncelikli ürün kuyruğu
```

İş kuralları framework bağımsız saf Python kodunda tutulur. Platform adaptörleri sadece kolon eşler; ürün adı, slug veya içerik alanlarını değiştirmez.

## Yol haritası

1. İyileştirme önerileri ve şablon üretimi
2. Search Console sorgu eşleştirmesi
3. Komut satırı aracı
4. Web paneli ve zamanlanmış denetimler

## AI destekli geliştirme

Bu proje AI destekli geliştirme araçları kullanılarak ilerletilmektedir. Mimari kararlar, iş kuralları, testler ve yayınlanan değişiklikler insan incelemesine açık şekilde GitHub geçmişinde tutulur.
