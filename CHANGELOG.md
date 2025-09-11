Changelog
Bu projedeki tüm önemli değişiklikler bu dosyada belgelenmektedir.

Format, Keep a Changelog standartlarına dayanmaktadır ve bu proje Semantic Versioning kullanmaktadır.

[Unreleased]
Henüz yayınlanmamış değişiklikler.

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

## [2.5.0] - 2025-09-11

### Eklendi (Added)

- `.github/workflows/docker-publish.yml` dosyası ile GitHub Actions entegrasyonu eklendi. Bu sayede `main` branch'ine yapılan her push'ta ve her yeni sürüm yayınlandığında Docker imajı otomatik olarak derlenip GHCR'ye yüklenir.

### Değiştirildi (Changed)

- **Mimari İyileştirme**: Scraper (`hdfilmcehennemi_scraper.py`) ve Service (`services.py`) katmanları arasındaki sorumluluklar net bir şekilde ayrıldı. Scraper artık sadece veri kazımaktan, Service katmanı ise veritabanı işlemlerinden sorumludur.
- **Docker İyileştirmeleri**:
  - `docker-compose.yml` dosyasındaki servis, imaj ve konteyner isimleri proje adıyla (`algo-video-bot`) tutarlı olacak şekilde standartlaştırıldı.
  - Docker volume yönetimi iyileştirildi; `database.db` ve `app.log` gibi dosyalar artık tek bir kalıcı veri klasörü (`/app/data`) altında yönetiliyor.
- `README.md` dosyası, yeni kurulum talimatları ve daha net açıklamalarla güncellendi.

### Düzeltildi (Fixed)

- `worker.py`: `movies` tablosunda bulunmayan `source_url` sütununu güncellemeye çalışan kritik bir SQL hatası düzeltildi.
- `hdfilmcehennemi_scraper.py` dosyasındaki `services.py`'de tekrar eden veritabanı fonksiyonları kaldırıldı.
- `worker.py` dosyasındaki dosya yolu oluşturma mantığından gereksiz değişkenler (`episode_num`, `season_num`) temizlendi.

## [2.1.0] - Önceki Sürüm

### Eklendi (Added)

- Dizi desteği: Dizi ana sayfa linki üzerinden tüm sezon ve bölümleri çekme ve indirme kuyruğuna ekleme özelliği.
- Ana sayfaya sekmeli yapı (Filmler / Diziler) eklendi.
- Disk kullanımını gösteren bir ilerleme çubuğu eklendi.
- Aktif indirmeleri özetleyen bir panel eklendi.

### Değiştirildi (Changed)

- Ana sayfa kullanıcı arayüzü (`index.html`) Tailwind CSS ile tamamen yenilendi.
- Durum güncellemeleri ve kullanıcı arayüzü etkileşimleri için JavaScript altyapısı iyileştirildi.
