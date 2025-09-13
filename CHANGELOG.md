Changelog
Bu projedeki tüm önemli değişiklikler bu dosyada belgelenmektedir.

Format, Keep a Changelog standartlarına dayanmaktadır ve bu proje Semantic Versioning kullanmaktadır.

[3.0.1] - 2025-09-13

### Eklendi (Added)

- `hdfilmcehennemi_worker`'a, sitenin kullandığı `devtools-detector.js` gibi anti-bot script'lerini yüklenmeden önce engelleyen bir mekanizma eklendi. Bu, indirme oturumunun (session) ve çerezlerin (cookie) geçersiz kılınmasını önler.

### Değiştirildi (Changed)

- `hdfilmcehennemi_worker` ve `izle_in_worker`, `undetected-chromedriver` ile `selenium-wire`'ı birleştiren daha kararlı ve güçlü bir hibrit sürücü modeli kullanacak şekilde tamamen yeniden düzenlendi. Bu standartlaşma, her iki worker'ın da en zorlu bot korumalarını aşmasını sağlar.
- `worker.py` içerisindeki `download_with_yt_dlp` fonksiyonu, tarayıcıdan gelen `Referer` ve `User-Agent` gibi kritik başlıkları `yt-dlp`'nin anladığı özel komutlarla (`--referer`, `--user-agent`) akıllıca iletecek şekilde iyileştirildi.

### Düzeltildi (Fixed)

- `hdfilmcehennemi` sitesindeki güncellenmiş bot korumaları nedeniyle tamamen çalışmaz hale gelen `hdfilmcehennemi_worker`'daki kritik hatalar giderildi. Tarayıcının çökmesi (`NoSuchWindowException`), zaman aşımına uğraması (`TimeoutError`) ve yanlış başlatma parametreleri (`InvalidArgumentException`) gibi bir dizi sorun çözüldü.
- `yt-dlp`'nin `403 Forbidden` (Yasak) ve `The downloaded file is empty` (İndirilen dosya boş) hataları almasına neden olan eksik kimlik bilgisi sorunu, tarayıcı başlıklarının ve çerezlerinin indirme aracına eksiksiz bir şekilde aktarılmasıyla çözüldü.

[3.0.0] - 2025-09-13

### Eklendi (Added)

- **Yeni Site Desteği: `izle.in`**
  - `izle.in` sitesinden film meta verilerini (başlık, yıl, özet, poster vb.) çekmek için `izle_in_scraper.py` adında yeni bir scraper eklendi.
  - Sistemin yeni siteyi tanıması için `config.py` ve `scrapers/__init__.py` dosyaları güncellendi.

### Değiştirildi (Changed)

- **Mimarinin Yeniden Yapılandırılması: Modüler Worker Yapısı**
  - Sizin öneriniz üzerine, her site için ayrı bir "worker" mantığı oluşturularak projenin mimarisi daha modüler ve sürdürülebilir hale getirildi. Bu, gelecekte yeni siteler eklendiğinde mevcut kodun bozulma riskini ortadan kaldırır.
  - `workers` adında yeni bir klasör ve tüm worker'ların uyması gereken `workers/base_worker.py` şablonu oluşturuldu.
  - `hdfilmcehennemi` ve `izle.in` siteleri için sırasıyla `workers/hdfilmcehennemi_worker.py` ve `workers/izle_in_worker.py` adında özel worker dosyaları oluşturuldu.
  - Gelen URL'ye göre doğru worker'ı seçen bir fabrika (`workers/__init__.py`) eklendi.
  - Ana `worker.py` dosyası, siteye özel tüm mantıklardan arındırılarak sadece süreci yöneten temiz bir yapıya kavuşturuldu.

### Düzeltildi (Fixed)

- **`izle.in` Entegrasyonundaki Gelişmiş Koruma Mekanizmaları Aşıldı:**
  - Sitenin, otomasyon araçlarını tespit ettiğinde video oynatıcıyı gizlediği anlaşıldı.
  - `undetected-chromedriver` kütüphanesi entegre edilerek tarayıcının bot olarak algılanması engellendi.
  - Video oynatıcının `devtools-console-detectv2.js` adında özel bir güvenlik script'i ile korunduğu tespit edildi.
  - `selenium-wire`'ın `block_requests` özelliği kullanılarak bu güvenlik script'inin yüklenmesi engellendi ve koruma mekanizması tamamen aşıldı.

- **`hdfilmcehennemi` Worker Hatası Giderildi:**
  - `izle.in` için yapılan geliştirmeler sırasında bozulan `hdfilmcehennemi` worker'ı, modüler mimari sayesinde orijinal ve kararlı çalışan haline geri döndürüldü.
  - Her site için ayrı webdriver yapılandırması kullanılarak kütüphaneler arası çakışmaların önüne geçildi.
  - Modülerleştirme sırasında eksik kalan `import re` ifadesi `hdfilmcehennemi_worker.py` dosyasına eklenerek `NameError` hatası düzeltildi.

[2.7.0] - 2025-09-11
Eklendi (Added)
Dizi Takip Özelliği:

Kullanıcıların dizileri "Takip Et" olarak işaretlemesine olanak tanıyan bir özellik eklendi.

Takip edilen diziler için günde bir kez otomatik olarak yeni bölüm kontrolü yapan bir zamanlayıcı (APScheduler) entegre edildi.

Yeni bulunan bölümler otomatik olarak indirme sırasına eklenir.

Otomatik Veritabanı Güncelleme (Migration): Uygulama başlatıldığında veritabanı şemasını kontrol eden ve is_tracked gibi eksik sütunları otomatik olarak ekleyen bir mekanizma (run_migrations) eklendi. Bu, gelecekteki güncellemeleri kolaylaştırır ve no such column hatalarını önler.

Değiştirildi (Changed)
Veritabanı (database.py): series tablosuna, bir dizinin takip edilip edilmediğini saklamak için is_tracked adında yeni bir sütun eklendi.

Arayüz (index.html): Her dizi kartına "Takip Et" onay kutusu (checkbox) eklendi ve bu kutunun tıklama olayının akordiyon menüsünü tetiklemesi engellendi.

Servisler (services.py): Takip edilen dizileri periyodik olarak kontrol edip yeni bölümleri veritabanına ekleyen check_and_add_new_episodes fonksiyonu eklendi.

Ana Uygulama (app.py): Zamanlayıcıyı başlatmak ve "Takip Et" durumunu güncellemek için /series/track adında yeni bir API endpoint'i eklendi.

Düzeltildi (Fixed)
Veritabanı Hatası: Uygulama güncellendiğinde ortaya çıkan sqlite3.OperationalError: no such column: is_tracked hatası, otomatik veritabanı güncelleme mekanizması ile kalıcı olarak çözüldü.

Arayüz Hatası: "Takip Et" onay kutusunun, üst katmandaki tıklama olayını tetiklediği için çalışmaması sorunu event.stopPropagation() kullanılarak düzeltildi.

[2.6.0] - 2025-09-11
Eklendi (Added)
Gelişmiş Klasör Yönetimi:

Film ve diziler için ayrı indirme klasörleri belirleme özelliği eklendi.

Tüm indirmelerin önce geçici bir klasöre (temp) yapılıp, tamamlandıktan sonra nihai hedef klasörüne taşınmasını sağlayan sağlam bir mekanizma eklendi. Bu sayede yarım kalan indirmelerin ana arşivi kirletmesi önlendi.

Yeni Ayarlar: Ayarlar menüsüne Film İndirme Klasörü, Dizi İndirme Klasörü ve Geçici İndirme Klasörü için yeni düzenlenebilir alanlar eklendi.

Değiştirildi (Changed)
Worker (worker.py) Mantığı: İndirme (process_video) fonksiyonu, dosyaları önce geçici bir klasöre indirecek ve indirme başarılı olduğunda shutil.move kullanarak hedefe taşıyacak şekilde tamamen yeniden yazıldı.

Veritabanı (database.py): settings tablosu, tek bir DOWNLOADS_FOLDER yerine MOVIES_DOWNLOADS_FOLDER, SERIES_DOWNLOADS_FOLDER ve TEMP_DOWNLOADS_FOLDER anahtarlarını destekleyecek şekilde güncellendi.

Ayarlar Arayüzü (settings.html): Web arayüzü, yeni klasör yönetimi ayarlarını yansıtacak şekilde güncellendi.

[2.5.0] - 2025-09-11
Eklendi (Added)
.github/workflows/docker-publish.yml dosyası ile GitHub Actions entegrasyonu eklendi. Bu sayede main branch'ine yapılan her push'ta ve her yeni sürüm yayınlandığında Docker imajı otomatik olarak derlenip GHCR'ye yüklenir.

Değiştirildi (Changed)
Mimari İyileştirme: Scraper (hdfilmcehennemi_scraper.py) ve Service (services.py) katmanları arasındaki sorumluluklar net bir şekilde ayrıldı.

Docker İyileştirmeleri: docker-compose.yml ve Docker volume yönetimi standartlaştırıldı.

README.md dosyası güncellendi.

Düzeltildi (Fixed)
Çeşitli SQL ve dosya yolu oluşturma hataları düzeltildi.

[2.1.0] - Önceki Sürüm
Eklendi (Added)
Dizi desteği, sekmeli yapı, disk kullanım çubuğu ve aktif indirme paneli eklendi.

Değiştirildi (Changed)
Kullanıcı arayüzü Tailwind CSS ile yenilendi.
