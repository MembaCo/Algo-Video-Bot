Changelog
Bu projedeki tüm önemli değişiklikler bu dosyada belgelenmektedir.

Format, Keep a Changelog standartlarına dayanmaktadır ve bu proje Semantic Versioning kullanmaktadır.

[Unreleased]
Henüz yayınlanmamış değişiklikler.

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
