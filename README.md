<p align="center">
<img src="https://placehold.co/800x200/111827/7c3aed?text=Algo-Video-Bot" alt="Algo-Video-Bot Banner">
</p>

<h1 align="center">Algo-Video-Bot: Gelişmiş Video İndirme Yöneticisi</h1>

<p align="center">
Modern ve dinamik video sitelerinden içerik indirmeyi otomatikleştiren, web tabanlı bir yönetim paneli.
</p>

<p align="center">
<a href="https://github.com/MembaCo/Algo-Video-Bot/actions/workflows/docker-publish.yml">
<img src="https://github.com/MembaCo/Algo-Video-Bot/actions/workflows/docker-publish.yml/badge.svg" alt="Docker Image CI">
</a>
<a href="https://github.com/MembaCo/Algo-Video-Bot/blob/main/LICENSE">
<img src="https://img.shields.io/badge/license-MIT-blue.svg" alt="License">
</a>
</p>

Algo-Video-Bot, modern ve dinamik video sitelerinden içerik indirmeyi otomatikleştiren, web tabanlı bir yönetim paneline sahip gelişmiş bir Python uygulamasıdır. Kullanıcıların video linklerini (tek tek veya toplu olarak) ekleyip indirme işlemlerini (başlatma, durdurma, silme, otomatik indirme) modern bir koyu tema arayüzü üzerinden yönetmelerini sağlar.

Proje, Docker ile paketlenmiş olup, GitHub Actions aracılığıyla otomatik olarak derlenir ve herhangi bir sunucuda veya CasaOS gibi platformlarda kolayca dağıtılabilir.

🚀 Temel Özellikler
Modern ve Koyu Arayüz: Videoları eklemek, kuyruğu yönetmek ve indirme durumlarını canlı olarak izlemek için kullanıcı dostu bir panel.

Güvenli ve Yönetilebilir Giriş: Panele erişimi korumak için hash'lenmiş parola sistemi ve arayüzden parola değiştirme imkanı.

Akıllı Bilgi Çekme: Sıraya eklenen her video için film adı, yılı, türü, özeti, IMDb puanı, yönetmen, oyuncular ve poster resmi gibi zengin meta verileri otomatik olarak siteden çeker.

Esnek Video Ekleme:

Tekli Ekleme: Tek bir film URL'si ile video ekleme.

Toplu Ekleme: Bir kategori veya arşiv sayfasının URL'si ile o sayfadaki tüm videoları tek seferde kuyruğa ekleme.

Gelişmiş Ayarlar Paneli:

İndirme klasörünü, dosya adı şablonunu, eşzamanlı indirme sayısını ve hız limitini arayüzden yönetme.

Otomatik İndirme Yöneticisi: Kuyruğa eklenen videoları, aktif edildiğinde sırayla ve belirlenen eşzamanlı indirme limitine göre otomatik olarak indirir.

Dayanıklı Web Kazıma (Scraping):

Site yapısı değişikliklerine karşı hibrit bir yaklaşım kullanır: Öncelikli olarak güvenilir JSON-LD verisini okur, başarısız olursa standart HTML etiketlerini analiz eder.

Selenium-wire kullanarak JavaScript ile korunan ve dinamik olarak yüklenen video kaynaklarını bulur.

Güvenilir Video İndirme:

yt-dlp entegrasyonu ile en karmaşık video akışlarını (.m3u8 vb.) indirir.

Docker ile Kolay Dağıtım: GitHub Actions ile otomatik olarak derlenen Docker imajı sayesinde tek komutla kurulum ve çalıştırma.

⚙️ Kurulum ve Çalıştırma
Yerel Makine (Geliştirme için)
Projeyi Klonlayın:

git clone <https://github.com/MembaCo/Algo-Video-Bot.git>
cd Algo-Video-Bot

Gerekli Kütüphaneleri Yükleyin: (Sanal ortam kullanılması tavsiye edilir)

pip install -r requirements.txt

.env Dosyasını Oluşturun: Proje ana dizininde .env adında bir dosya oluşturun.

Parola Hash'i Üretin: Terminalde aşağıdaki komutları çalıştırarak güvenli bir parola hash'i oluşturun ve çıktıyı kopyalayın.

python -c "from werkzeug.security import generate_password_hash; print(generate_password_hash('SENIN_GUVENLI_PAROLAN'))"

.env Dosyasını Doldurun:

SECRET_KEY="COK_GIZLI_VE_GUCLU_BIR_ANAHTAR_BURAYA_YAZIN"
ADMIN_USERNAME="admin"
ADMIN_PASSWORD_HASH="<BURAYA_KOPYALADIGINIZ_HASH_GELECEK>"

Uygulamayı Başlatın:

python app.py

Uygulama, varsayılan olarak <http://127.0.0.1:5000> adresinde çalışmaya başlayacaktır.

🐳 Docker ile Dağıtım (Tavsiye Edilen)
Bu proje, GitHub Actions kullanılarak otomatik olarak bir Docker imajı olarak derlenir ve GitHub Container Registry (GHCR) üzerinde yayınlanır.

Standart Sunucu Kurulumu
Docker Kurulumu: Sunucunuzda Docker'ın kurulu olduğundan emin olun.

Gerekli Dosyaları Hazırlayın:

mkdir algo-video-bot && cd algo-video-bot
mkdir downloads
touch database.db app.log

.env Dosyasını Oluşturun: Yukarıdaki "Yerel Kurulum" bölümünde anlatıldığı gibi .env dosyanızı oluşturun ve doldurun.

Docker İmajını Çekin (Pull):

docker pull ghcr.io/MembaCo/Algo-Video-Bot:latest

Konteyneri Çalıştırın:

docker run -d \
  -p 5000:5000 \
  --name algo-video-bot \
  --restart unless-stopped \
  -v ./downloads:/app/downloads \
  -v ./database.db:/app/database.db \
  -v ./app.log:/app/app.log \
  --env-file ./.env \
  --shm-size=2g \
  ghcr.io/MembaCo/Algo-Video-Bot:latest

Erişim: Artık uygulamaya http://SUNUCU_IP_ADRESINIZ:5000 adresinden erişebilirsiniz.

CasaOS Kurulumu
App Store'u Aç: CasaOS arayüzünde "App Store"a gidin.

Custom Install (Özel Kurulum): Sağ üst köşedeki "Custom Install" butonuna tıkla.

İçe Aktar (Import): Açılan pencerede "Import" seçeneğine tıkla.

Yapılandırmayı Yapıştır: Aşağıdaki docker-compose.yml kodunun tamamını kopyala ve metin kutusuna yapıştır. Ardından "Submit" butonuna bas.

services:
  algo-video-bot:
    image: ghcr.io/membaco/algo-video-bot:latest
    container_name: algo-video-bot
    ports:
      - 5000:5000
    volumes:
      - type: bind
        source: /DATA/AppData/algo-video-bot/downloads
        target: /app/downloads
      - type: bind
        source: /DATA/AppData/algo-video-bot/database.db
        target: /app/database.db
      - type: bind
        source: /DATA/AppData/algo-video-bot/app.log
        target: /app/app.log
    environment:
      - SECRET_KEY= # Buraya çok gizli ve rastgele bir anahtar yazın
      - ADMIN_USERNAME=admin
      - ADMIN_PASSWORD_HASH= # Buraya ürettiğiniz parola hash'ini yapıştırın
    restart: unless-stopped
    shm_size: 2g
    x-casaos:
      architectures:
        - amd64
      main: algo-video-bot
      description:
        en_us: Web tabanlı video indirme yöneticisi.
      tagline:
        en_us: Kişisel Video İndirme Yöneticiniz
      developer: MembaCo
      author: MembaCo
      icon: <https://raw.githubusercontent.com/walkxcode/dashboard-icons/main/png/movie-clapper.png>
      title:
        en_us: Algo Video Bot
      category: Utilities
      port_map: "5000"

Ayarları Doldur: CasaOS, yapılandırmayı okuyacak ve sana doldurman için alanlar gösterecektir:

SECRET_KEY: Bu alana, bir parola üretici kullanarak oluşturduğun uzun ve rastgele bir metin yapıştır.

ADMIN_PASSWORD_HASH: Bu alana, daha önce ürettiğin parola hash'ini yapıştır.

Kurulumu Tamamla: Tüm alanları doldurduktan sonra sağ alttaki "Install" butonuna bas.

💻 Kullanılan Teknolojiler
Backend: Python, Flask

Web Scraping & Otomasyon: Selenium, Selenium-Wire, BeautifulSoup

Video İndirme: yt-dlp

Frontend: HTML, Tailwind CSS, JavaScript (Fetch API)

Veritabanı: SQLite

Proses Yönetimi: Multiprocessing, Threading

Dağıtım: Docker, GitHub Actions

<p align="center">
Bu proje, <strong>MembaCo.</strong> tarafından geliştirilmiştir.
</p>
