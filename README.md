# Türkmopet SEO Content Engine

Motosiklet yedek parça kataloglarında ürün adı ve slug alanlarına dokunmadan SEO içerik kalitesini analiz eden Python araç seti.

## İlk modül: katalog SEO denetçisi

`audit_product` fonksiyonu ürün kaydını yalnızca analiz eder; ürün adı veya slug üzerinde değişiklik yapmaz. Böylece mevcut URL'ler, pazaryeri eşleşmeleri ve katalog kimliği korunur.

Kontrol edilen alanlar:

- ürün adı ve slug zorunluluğu
- meta başlık uzunluğu
- meta açıklama uzunluğu
- ürün açıklaması yeterliliği
- meta başlıkta ürün adı bağlamı
- meta açıklamada marka bağlamı
- açıklamada kategori bağlamı

Sonuç olarak 0–100 kalite puanı ve alan bazlı hata listesi döner.

## Kurulum

```bash
python -m pip install -e .
```

## Kullanım

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

## Test

```bash
python -m unittest discover -s tests -v
python -m compileall -q src tests
```

CI, pull request ve `main` pushlarında Python 3.11, 3.12 ve 3.13 üzerinde çalışır.

## Mimari

```text
ProductRecord
    ↓
audit_product
    ↓
AuditResult
    ├── score
    └── AuditIssue[]
```

İş kuralları framework bağımsız saf Python kodunda tutulur. Bu sayede ileride CSV/Excel adaptörü, web arayüzü veya Shopify/İkas dışa aktarım işleyicisi aynı çekirdeği kullanabilir.

## Yol haritası

1. CSV ve Excel toplu analiz
2. Ürün, kategori ve marka raporları
3. Tekrarlanan meta içerik tespiti
4. İyileştirme önerileri ve şablon üretimi
5. Search Console sorgu eşleştirmesi

## AI destekli geliştirme

Bu proje AI destekli geliştirme araçları kullanılarak ilerletilmektedir. Mimari kararlar, iş kuralları, testler ve yayınlanan değişiklikler insan incelemesine açık şekilde GitHub geçmişinde tutulur.
