Flask ile Gelişmiş Video İndirme Yöneticisi
Bu proje, hdfilmcehennemi.ltd gibi modern ve dinamik video sitelerinden içerik indirmeyi otomatikleştiren, web tabanlı bir yönetim paneline sahip gelişmiş bir Python uygulamasıdır. Kullanıcıların video linklerini ekleyip indirme işlemlerini (başlatma, durdurma, silme) bir web arayüzü üzerinden yönetmelerini sağlar.

(Not: Bu kısmı kendi ekran görüntünüzün URL'si ile güncelleyebilirsiniz.)

🚀 Temel Özellikler
Web Tabanlı Yönetim Paneli: Videoları eklemek ve indirme kuyruğunu yönetmek için modern ve kullanıcı dostu bir arayüz.

Güvenli Giriş Sistemi: Panele erişimi korumak için basit kullanıcı adı ve şifre doğrulama.

Dinamik Bilgi Çekme: Sıraya eklenen her video için film adı, yılı ve türü gibi meta verileri otomatik olarak siteden çeker.

Akıllı Dosya Adlandırma: İndirilen videoları, çekilen meta verilere göre (Film Adı - Yıl - Tür.mp4 formatında) otomatik olarak isimlendirir.

Gelişmiş İndirme Kontrolü:

İndirmeleri tek bir tıkla başlatın.

Devam eden indirmeleri durdurun (duraklatın) ve daha sonra devam ettirin.

Kuyruktaki veya tamamlanmış indirmeleri silin.

Canlı Durum Takibi: Web arayüzü, indirme durumunu (Kaynak aranıyor..., İndiriliyor, Tamamlandı, Hata) ve indirme ilerlemesini (%) her birkaç saniyede bir otomatik olarak günceller.

Arka Plan İşlemleri: Uzun süren indirme işlemleri, web arayüzünün donmasını engellemek için arka planda ayrı prosesler olarak çalışır.

Gelişmiş Scraping Yetenekleri:

Selenium-wire kullanarak JavaScript ile korunan ve dinamik olarak yüklenen video kaynaklarını bulur.

Gizli ağ trafiğini dinleyerek en karmaşık video akış adreslerini (.m3u8, manifest.txt vb.) tespit eder.

yt-dlp entegrasyonu ile Referer ve User-Agent gibi güvenlik kontrollerini aşarak indirme yapar.

🛠️ Proje Mimarisi
app.py: Ana Flask uygulaması. Web sunucusunu çalıştırır, kullanıcı arayüzünü sunar, veritabanı işlemlerini yönetir ve arka plan indirme proseslerini tetikler.

worker.py: Arka plan işçisi. app.py tarafından her bir indirme için özel olarak çağrılır. Selenium ile video kaynağını bulur ve yt-dlp ile indirme işlemini gerçekleştirir.

templates/: Web arayüzünü oluşturan HTML şablonlarını içerir.

login.html: Giriş sayfası.

index.html: Ana yönetim paneli.

database.db: İndirme kuyruğundaki videoların bilgilerini ve durumlarını saklayan SQLite veritabanı.

downloads/: İndirilen videoların kaydedildiği klasör.

⚙️ Kurulum ve Çalıştırma
Projeyi yerel makinenizde çalıştırmak için aşağıdaki adımları izleyin:

1. Projeyi Klonlayın:

git clone https://github.com/kullanici-adiniz/proje-adiniz.git
cd proje-adiniz

2. Gerekli Kütüphaneleri Yükleyin:
Bir sanal ortam oluşturmanız tavsiye edilir.

# Sanal ortam oluşturma (isteğe bağlı ama önerilir)
python -m venv venv
source venv/bin/activate  # Linux/macOS için
# venv\Scripts\activate    # Windows için

# Gerekli kütüphaneleri yükle
pip install -r requirements.txt

3. Yönetici Bilgilerini Ayarlayın:
app.py dosyasını açın ve ADMIN_USERNAME ile ADMIN_PASSWORD değişkenlerini kendi istediğiniz bilgilerle güncelleyin.

4. Uygulamayı Başlatın:
Uygulamayı çalıştırmak için aşağıdaki komutu terminalde çalıştırın:

python app.py

Uygulama, varsayılan olarak http://127.0.0.1:5000 adresinde çalışmaya başlayacaktır.

🖥️ Nasıl Kullanılır?
Tarayıcınızı açın ve http://127.0.0.1:5000 adresine gidin.

Belirlediğiniz kullanıcı adı ve şifre ile giriş yapın.

İndirmek istediğiniz hdfilmcehennemi.ltd linkini forma yapıştırın ve "Sıraya Ekle" butonuna tıklayın. Film bilgileri çekilecek ve kuyruğa eklenecektir.

İndirmek istediğiniz videonun yanındaki "Başlat" butonuna tıklayın.

İşlemin durumunu ve ilerlemesini arayüzden canlı olarak takip edin. İndirme tamamlandığında video, downloads klasörüne kaydedilecektir.

💻 Kullanılan Teknolojiler
Backend: Python, Flask

Web Scraping & Otomasyon: Selenium, Selenium-Wire, BeautifulSoup

Video İndirme: yt-dlp

Frontend: HTML, Tailwind CSS, JavaScript (Fetch API)

Veritabanı: SQLite

Proses Yönetimi: Multiprocessing

Bu proje, MembaCo. tarafından geliştirilmiştir.