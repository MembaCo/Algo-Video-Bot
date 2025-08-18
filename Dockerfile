# @author: MembaCo.

# Temel imaj olarak Python 3.11'in hafif bir sürümünü kullanıyoruz.
FROM python:3.11-slim

# Konteyner içindeki çalışma dizinini belirliyoruz.
WORKDIR /app

# Sistem paket listesini güncelliyor ve gerekli araçları yüklüyoruz.
RUN apt-get update && apt-get install -y \
    wget \
    unzip \
    --no-install-recommends \
    && rm -rf /var/lib/apt/lists/*

# Google Chrome'un en son stabil sürümünü indirip kuruyoruz.
RUN wget -q https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb \
    && apt-get update \
    && apt-get install -y ./google-chrome-stable_current_amd64.deb \
    --no-install-recommends \
    && rm -f google-chrome-stable_current_amd64.deb

# --- GÜNCELLEME ---
# ChromeDriver'ı otomatik bulmak yerine, bilinen stabil bir sürümü doğrudan indiriyoruz.
# Bu yöntem, dış API değişikliklerine karşı çok daha dayanıklıdır.
RUN wget -q --continue -P /tmp https://storage.googleapis.com/chrome-for-testing-public/126.0.6478.126/linux64/chromedriver-linux64.zip \
    && unzip -q /tmp/chromedriver-linux64.zip -d /usr/bin \
    && chmod +x /usr/bin/chromedriver-linux64/chromedriver \
    && ln -s /usr/bin/chromedriver-linux64/chromedriver /usr/bin/chromedriver \
    && rm /tmp/chromedriver-linux64.zip
# --- GÜNCELLEME SONU ---

# Python bağımlılıklarını kuruyoruz.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Projenin geri kalan tüm dosyalarını çalışma dizinine kopyalıyoruz.
COPY . .

# Flask uygulaması için 5000 portunu açıyoruz.
EXPOSE 5000

# Konteyner başlatıldığında çalıştırılacak komut.
CMD ["python", "app.py"]
