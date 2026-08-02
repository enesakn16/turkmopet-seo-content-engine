# Search Console fırsat önceliklendirmesi

`search_console` modülü, katalog SEO denetimini gerçek Google Search Console talebiyle birleştirir. Amaç sadece düşük puanlı ürünleri değil, yüksek gösterim alıp düşük tıklama üreten ürünleri öncelemektir.

## Girdi

Google Search Console sorgu dışa aktarımı İngilizce veya Türkçe kolon başlıklarıyla okunabilir:

```text
query,page,clicks,impressions,ctr,position
```

veya:

```text
Sorgu,Sayfa,Tıklamalar,Gösterimler,TO,Konum
```

`ctr` alanı `0.04`, `4` veya `%4` biçimlerinde kabul edilir.

## Kullanım

```python
from turkmopet_seo import (
    audit_catalog,
    prioritize_search_opportunities,
    read_platform_catalog_csv,
    read_search_console_csv,
    write_search_opportunities_csv,
)

products = read_platform_catalog_csv("ikas-products.csv", "ikas")
report = audit_catalog(products)
search_rows = read_search_console_csv("search-console.csv")
opportunities = prioritize_search_opportunities(report, search_rows)
write_search_opportunities_csv(
    opportunities,
    "reports/search-opportunities.csv",
)
```

## Eşleştirme kuralı

Search Console sayfa URL'sinin son yol parçası ürün slug'ıyla eşleştirilir. Sorgu parametreleri ve sondaki `/` sonucu etkilemez. Eşleşmeyen URL'ler güvenli biçimde atlanır; ürün adı veya slug değiştirilmez.

## Öncelik puanı

Puan şu sinyalleri birlikte değerlendirir:

- gösterim sayısı
- gerçekleşmeyen tıklama potansiyeli (`1 - CTR`)
- ortalama konum
- katalog SEO kalite açığı

4–20 arasındaki ortalama konumlar, içerik iyileştirmesiyle sonuç alma ihtimali daha yüksek olduğu için en güçlü katsayıyı alır. İlk üç sıradaki sayfalar daha düşük, 20 sıra gerisindeki sayfalar ise daha temkinli katsayıyla değerlendirilir.

## Çıktı

```text
row_number,name,slug,audit_score,clicks,impressions,ctr,average_position,query_count,top_query,opportunity_score
```

Çıktı Excel uyumlu UTF-8 BOM ile yazılır ve `opportunity_score` azalan sırada döner. Bu rapor otomatik içerik güncellemesi yapmaz; yalnızca inceleme sırası üretir.
