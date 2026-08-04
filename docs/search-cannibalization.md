# Search Console anahtar kelime kanibalizasyon raporu

Aynı sorgunun birden fazla ürün veya kategori sayfasına dağılması, Google'ın hangi URL'yi öne çıkaracağı konusunda kararsız kaldığını gösterebilir. `seo-cannibalization` Search Console CSV dışa aktarımını sorgu ve normalize edilmiş URL yolu bazında toplar; aynı sorguda en az iki sayfa bulunan kümeleri raporlar.

## Kullanım

```bash
seo-cannibalization \
  --input exports/search-console.csv \
  --output reports/cannibalization.csv
```

Varsayılan olarak toplam gösterimi 50'nin altında kalan sorgular ve yalnızca tek sayfası olan sorgular rapora alınmaz. Eşikler değiştirilebilir:

```bash
seo-cannibalization \
  --input exports/search-console.csv \
  --output reports/cannibalization.csv \
  --minimum-impressions 100 \
  --minimum-pages 2
```

## Öncelik sınıfları

- `critical`: Lider sayfa toplam gösterimlerin %60'ından azını alıyor; talep ciddi biçimde bölünmüş.
- `warning`: Lider sayfanın payı %60–80 arasında.
- `review`: Lider sayfa %80 veya daha fazla paya sahip; ikincil URL yine de incelenmeli.

Rapor, kritik sorguları ve yüksek gösterimli kümeleri önce sıralar. Her sorgu için tüm rekabet eden URL'ler ayrı satırlarda yazılır.

## Çıktı alanları

```text
query,severity,page_count,total_clicks,total_impressions,leading_page,leading_share,page,slug,clicks,impressions,ctr,average_position
```

CSV UTF-8 BOM ile üretilir ve Excel'de doğrudan açılabilir.

## Çıkış kodları

- `0`: Çakışma bulunmadı.
- `1`: En az bir çakışma bulundu; rapor üretildi.
- `2`: Girdi, eşik veya dosya hatası.

Araç hiçbir URL'yi, slug'ı veya içeriği otomatik değiştirmez. Rapor; birleştirme, canonical, iç bağlantı veya sorgu niyeti ayrıştırma kararları için insan inceleme kuyruğudur.
