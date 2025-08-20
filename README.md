# Flask ile Gelişmiş Video İndirme Yöneticisi v1.0.0

Bu proje, modern ve dinamik video sitelerinden (şu anda `hdfilmcehennemi.ltd` desteklenmektedir) içerik indirmeyi otomatikleştiren, web tabanlı bir yönetim paneline sahip gelişmiş bir Python uygulamasıdır. Kullanıcıların video linklerini ekleyip indirme işlemlerini (başlatma, durdurma, silme, otomatik indirme) bir web arayüzü üzerinden yönetmelerini sağlar.

![Uygulama Arayüzü](https://i.imgur.com/example.png)
*(Not: Bu kısmı kendi ekran görüntünüzün URL'si ile güncelleyebilirsiniz.)*

---

## 🚀 Temel Özellikler

- **Modern Web Arayüzü:** Videoları eklemek, kuyruğu yönetmek ve indirme durumlarını canlı olarak izlemek için kullanıcı dostu bir panel.
- **Güvenli Giriş Sistemi:** Panele erişimi korumak için basit kullanıcı adı ve şifre doğrulama.
- **Akıllı Bilgi Çekme:** Sıraya eklenen her video için film adı, yılı, türü, özeti, IMDb puanı, yönetmen, oyuncular ve poster resmi gibi zengin meta verileri otomatik olarak siteden çeker.
- **Otomatik İndirme Yöneticisi:** Kuyruğa eklenen videoları, aktif edildiğinde sırayla ve otomatik olarak indirir.
- **Gelişmiş İndirme Kontrolü:**
  - İndirmeleri tek bir tıkla başlatın.
  - Devam eden indirmeleri durdurun (duraklatın).
  - Kuyruktaki kayıtları veya tamamlanmış indirmelerin sadece kaydını silin.
  - **Disk'ten Sil:** İndirilmiş video dosyasını doğrudan arayüzden kalıcı olarak silin.
- **Canlı Durum Takibi:** Web arayüzü, indirme durumunu (Kaynak aranıyor..., İndiriliyor, Tamamlandı, Hata) ve indirme ilerlemesini (%) anlık olarak günceller.
- **Arka Plan İşlemleri:** Uzun süren indirme işlemleri, web arayüzünün donmasını engellemek için arka planda ayrı prosesler (`multiprocessing`) olarak çalışır.
- **Dayanıklı Web Kazıma (Scraping):**
  - Site yapısı değişikliklerine karşı hibrit bir yaklaşım kullanır: Öncelikli olarak güvenilir **JSON-LD** verisini okur, başarısız olursa standart **HTML** etiketlerini analiz eder.
  - `Selenium-wire` kullanarak JavaScript ile korunan ve dinamik olarak yüklenen video kaynaklarını bulur.
- **Güvenilir Video İndirme:**
  - `yt-dlp` entegrasyonu ile en karmaşık video akışlarını (`.m3u8` vb.) indirir.
  - Sunucu taraflı korumaları (`403 Forbidden` vb.) aşmak için tarayıcıdan aldığı **çerez (cookie) ve header** bilgilerini otomatik olarak kullanır.
- **Modüler ve Genişletilebilir Mimari:** Proje, gelecekte farklı video siteleri için yeni modüller eklemeyi kolaylaştıracak şekilde tasarlanmıştır.

---

## 🛠️ Proje Mimarisi

- **`app.py`**: Ana Flask uygulaması. Web sunucusunu çalıştırır, kullanıcı arayüzünü sunar, veritabanı işlemlerini yönetir ve arka plan indirme proseslerini tetikler. Otomatik indirme yöneticisini barındırır.
- **`worker.py`**: Arka plan işçisi. `app.py` tarafından her bir indirme için özel olarak çağrılır. Selenium ile video kaynağını bulur ve `yt-dlp` ile indirme işlemini gerçekleştirir.
- **`config.py`**: Tüm yapılandırma ayarlarının (giriş bilgileri, veritabanı adı, versiyon vb.) merkezileştirildiği dosya.
- **`database.py`**: Veritabanı bağlantısı ve kurulum mantığını içeren modül.
- **`logging_config.py`**: Tüm uygulama için merkezi loglama yapılandırmasını yönetir. Logları hem konsola hem de `app.log` dosyasına yazar.
- **`templates/`**: Web arayüzünü oluşturan HTML şablonlarını içerir.
- **`database.db`**: İndirme kuyruğundaki videoların bilgilerini ve durumlarını saklayan SQLite veritabanı.
- **`downloads/`**: İndirilen videoların kaydedildiği klasör.

---

## ⚙️ Kurulum ve Çalıştırma

1. **Projeyi Klonlayın:**

    ```bash
    git clone [https://github.com/kullanici-adiniz/proje-adiniz.git](https://github.com/kullanici-adiniz/proje-adiniz.git)
    cd proje-adiniz
    ```

2. **Gerekli Kütüphaneleri Yükleyin:**
    *(Bir sanal ortam (virtual environment) oluşturmanız şiddetle tavsiye edilir.)*

    ```bash
    # Sanal ortam oluşturma (isteğe bağlı ama önerilir)
    python -m venv venv
    source venv/bin/activate  # Linux/macOS için
    # venv\Scripts\activate    # Windows için

    # Gerekli kütüphaneleri yükle
    pip install -r requirements.txt
    ```

3. **Yönetici Bilgilerini Ayarlayın:**
    `config.py` dosyasını açın ve `ADMIN_USERNAME` ile `ADMIN_PASSWORD` değişkenlerini kendi istediğiniz bilgilerle güncelleyin.

4. **Uygulamayı Başlatın:**

    ```bash
    python app.py
    ```

    Uygulama, varsayılan olarak `http://127.0.0.1:5000` adresinde çalışmaya başlayacaktır.

---

## 🖥️ Nasıl Kullanılır?

1. Tarayıcınızı açın ve `http://127.0.0.1:5000` adresine gidin.
2. Belirlediğiniz kullanıcı adı ve şifre ile giriş yapın.
3. İndirmek istediğiniz `hdfilmcehennemi.ltd` linkini forma yapıştırın ve "Sıraya Ekle" butonuna tıklayın.
4. Videolarınız kuyruğa eklenecektir. İsterseniz "Otomatik İndirmeyi Başlat" butonuna tıklayarak tüm kuyruğun sırayla indirilmesini sağlayabilir veya her video için manuel olarak "Başlat" butonunu kullanabilirsiniz.
5. İşlemin durumunu ve ilerlemesini arayüzden canlı olarak takip edin.

---

## 💻 Kullanılan Teknolojiler

- **Backend:** Python, Flask
- **Web Scraping & Otomasyon:** Selenium, Selenium-Wire, BeautifulSoup
- **Video İndirme:** yt-dlp
- **Frontend:** HTML, Tailwind CSS, JavaScript (Fetch API)
- **Veritabanı:** SQLite
- **Proses Yönetimi:** Multiprocessing, Threading
- **Loglama:** Python `logging` modülü

🐳 Docker ile Dağıtım (Deployment)
Bu proje, GitHub Actions kullanılarak otomatik olarak bir Docker imajı olarak derlenir ve GitHub Container Registry (GHCR) üzerinde yayınlanır. Bu sayede uygulamayı herhangi bir sunucuda kolayca çalıştırabilirsiniz.

Sunucuda Çalıştırma Adımları
Docker Kurulumu: Sunucunuzda Docker'ın kurulu olduğundan emin olun.

Gerekli Dosyaları Hazırlayın: Uygulamanın verilerini (veritabanı, indirilen videolar, loglar) kalıcı olarak saklamak için bir klasör oluşturun.

# Proje için bir klasör oluşturun ve içine girin

mkdir algo-video-bot
cd algo-video-bot

# Gerekli alt klasörü ve boş dosyaları oluşturun

mkdir downloads
touch database.db
touch app.log

.env Dosyasını Oluşturun: Uygulamanın yapılandırma ayarları için bir .env dosyası oluşturun.

nano .env

İçeriğini aşağıdaki gibi doldurun ve güçlü bir parola hash'i ile güncelleyin:

SECRET_KEY="COK_GIZLI_VE_GUCLU_BIR_ANAHTAR_BURAYA_YAZIN"
ADMIN_USERNAME="admin"
ADMIN_PASSWORD_HASH="scrypt:32768:8:1$....BURAYA_URETTIGINIZ_HASH_GELECEK...."

Docker İmajını Çekin (Pull): Projenin en güncel imajını GHCR'den çekin.

docker pull ghcr.io/MembaCo/Algo-Video-Bot:latest

Konteyneri Çalıştırın: Aşağıdaki docker run komutu ile uygulamayı başlatın. Bu komut, oluşturduğunuz dosya ve klasörleri konteynere bağlayacak ve .env dosyasını kullanacaktır.

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

Yönetim Komutları
Logları Kontrol Etme:

docker logs -f algo-video-bot

Konteyneri Durdurma:

docker stop algo-video-bot

Konteyneri Başlatma:

docker start algo-video-bot

Konteyneri Silme:

docker rm algo-video-bot

Bu proje, **MembaCo.** tarafından geliştirilmiştir.
