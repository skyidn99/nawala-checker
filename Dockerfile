FROM python:3.11-slim

# Install Chromium dan driver untuk Selenium
RUN apt-get update && \
    apt-get install -y chromium chromium-driver && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy semua file dari repo ke dalam container
COPY . .

# Install library Python
RUN pip install --no-cache-dir -r requirements.txt

# Saat container dijalankan, otomatis jalankan script ini
CMD ["python", "check_domains.py"]
