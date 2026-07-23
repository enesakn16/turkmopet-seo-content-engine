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

Girdi dosyası UTF-8 veya Excel uyumlu UTF-8 BOM olabilir ve şu kolonları içermelidir:

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

## Test

```bash
python -m unittest discover -s tests -v
python -m compileall -q src tests
```

CI, pull request ve `main` pushlarında Python 3.11, 3.12 ve 3.13 üzerinde çalışır.

## Mimari

```text
CSV katalog dışa aktarımı
        ↓
read_catalog_csv
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
        ↓
write_audit_csv
```

İş kuralları framework bağımsız saf Python kodunda tutulur. Bu sayede ileride web arayüzü, Shopify/İkas dışa aktarım işleyicisi veya zamanlanmış raporlama aynı çekirdeği kullanabilir.

## Yol haritası

1. İkas ve Shopify kolon eşleme adaptörleri
2. Ürün, kategori ve marka özet raporları
3. İyileştirme önerileri ve şablon üretimi
4. Search Console sorgu eşleştirmesi
5. Web paneli ve zamanlanmış denetimler

## AI destekli geliştirme

Bu proje AI destekli geliştirme araçları kullanılarak ilerletilmektedir. Mimari kararlar, iş kuralları, testler ve yayınlanan değişiklikler insan incelemesine açık şekilde GitHub geçmişinde tutulur.
