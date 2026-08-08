# Search Console anahtar kelime kanibalizasyon raporu

Aynı sorgunun birden fazla ürün veya kategori sayfasına dağılması, Google'ın hangi URL'yi öne çıkaracağı konusunda kararsız kaldığını gösterebilir. `seo-cannibalization` Search Console CSV dışa aktarımını sorgu ve normalize edilmiş URL yolu bazında toplar; aynı sorguda en az iki anlamlı sayfa bulunan kümeleri raporlar.

## Kullanım

```bash
seo-cannibalization \
  --input exports/search-console.csv \
  --output reports/cannibalization.csv
```

Varsayılan olarak toplam gösterimi 50'nin altında kalan sorgular, yalnızca tek anlamlı sayfası olan sorgular ve 10 gösterimin altında kalan düşük sinyalli URL'ler rapora alınmaz. Eşikler değiştirilebilir:

```bash
seo-cannibalization \
  --input exports/search-console.csv \
  --output reports/cannibalization.csv \
  --minimum-impressions 100 \
  --minimum-pages 2 \
  --minimum-page-impressions 20
```

`--minimum-page-impressions`, aynı sorguda tesadüfen birkaç kez görünen filtre, parametreli sayfa veya zayıf URL'lerin sahte kanibalizasyon üretmesini engeller. Aynı URL'ye ait birden fazla Search Console satırı önce toplanır, eşik daha sonra uygulanır. Bu değer `--minimum-impressions` değerinden büyük olamaz.

## Öncelik sınıfları

- `critical`: Lider sayfa toplam gösterimlerin %60'ından azını alıyor; talep ciddi biçimde bölünmüş.
- `warning`: Lider sayfanın payı %60–80 arasında.
- `review`: Lider sayfa %80 veya daha fazla paya sahip; ikincil URL yine de incelenmeli.

Rapor, kritik sorguları ve yüksek gösterimli kümeleri önce sıralar. Her sorgu için eşik üstünde kalan rekabet eden URL'ler ayrı satırlarda yazılır.

## Önerilen aksiyonlar

Araç, her çakışmaya açıklanabilir bir `action_type` ve insan tarafından uygulanacak `recommended_action` ekler:

- `consolidate_or_canonical_review`: Lider payı %60'ın altındaysa veya üç ve daha fazla anlamlı URL yarışırken lider payı %80'in altında kalıyorsa sayfaları birleştirme ya da canonical kararını incele.
- `separate_search_intent`: İki URL arasında orta seviyeli rekabet varsa başlık, içerik ve iç bağlantıları farklı arama niyetlerine göre ayrıştır.
- `strengthen_leading_page`: Bir URL toplam gösterimlerin en az %80'ini alarak açıkça liderse, üç veya daha fazla URL görülse bile otomatik olarak konsolidasyon önerilmez; iç bağlantıları lider URL'ye yoğunlaştır ve ikincil URL'lerin gereksiz sorgu eşleşmesini incele.

URL sayısı tek başına birleştirme/canonical önerisi üretmez. Örneğin üç URL'de dağılım `%90 / %5 / %5` ise lider sayfa yeterince baskındır ve `strengthen_leading_page` önerilir; `%70 / %15 / %15` gibi daha dağınık bir kümede ise `consolidate_or_canonical_review` önerilir. Böylece yalnızca URL sayısı yüzünden gereksiz ve riskli konsolidasyon kararları öne çıkarılmaz.

Bu öneriler otomatik değişiklik yapmaz. Canonical, yönlendirme, ürün birleştirme veya içerik düzenleme kararı uygulanmadan önce URL'lerin ticari amacı doğrulanmalıdır.

## Çıktı alanları

```text
query,severity,action_type,recommended_action,page_count,total_clicks,total_impressions,leading_page,leading_share,page,slug,clicks,impressions,ctr,average_position
```

CSV UTF-8 BOM ile üretilir ve Excel'de doğrudan açılabilir.

## Çıkış kodları

- `0`: Çakışma bulunmadı.
- `1`: En az bir çakışma bulundu; rapor üretildi.
- `2`: Girdi, eşik veya dosya hatası.

Araç hiçbir URL'yi, slug'ı veya içeriği otomatik değiştirmez. Rapor; birleştirme, canonical, iç bağlantı veya sorgu niyeti ayrıştırma kararları için insan inceleme kuyruğudur.
