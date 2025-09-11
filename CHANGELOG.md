# Changelog

Bu projedeki tüm önemli değişiklikler bu dosyada belgelenmektedir.

Format, [Keep a Changelog](https://keepachangelog.com/en/1.0.0/) standartlarına dayanmaktadır ve bu proje [Semantic Versioning](https://semver.org/spec/v2.0.0.html) kullanmaktadır.

## [Unreleased]

- Henüz yayınlanmamış değişiklikler.

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