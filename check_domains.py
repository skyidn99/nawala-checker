import os
import requests

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from time import sleep
from datetime import datetime

DOMAINS_FILE = "domains.txt"

# Ambil token & chat id dari environment (diset di Railway Variables)
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")


def send_telegram(text: str):
    """Kirim pesan ke Telegram, kalau token & chat_id sudah di-set."""
    if not TELEGRAM_TOKEN or not TELEGRAM_CHAT_ID:
        print("Telegram belum dikonfigurasi (TOKEN / CHAT_ID kosong)")
        return

    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": text,
    }

    try:
        resp = requests.post(url, json=payload, timeout=10)
        if not resp.ok:
            print(
                f"Gagal kirim ke Telegram, status={resp.status_code}, body={resp.text}"
            )
    except Exception as e:
        print(f"Gagal kirim ke Telegram: {e}")


def setup_driver():
    options = Options()
    # mode headless: browser tidak kelihatan
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    driver = webdriver.Chrome(options=options)
    return driver


def load_domains():
    with open(DOMAINS_FILE) as f:
        return [line.strip() for line in f if line.strip()]


def classify_status_text(status_text: str):
    """
    Mengubah teks hasil dari Nawala menjadi emoji + label singkat.

    Nanti kalau perlu kita sesuaikan lagi kata kunci-nya
    berdasarkan teks asli di <div id="results">.
    """
    t = status_text.lower().strip()

    if not t:
        return "⚪", "TIDAK ADA DATA"

    # aman dulu
    if (
        "not blocked" in t
        or "tidak diblokir" in t
        or "not in our list" in t
        or "clean" in t
        or "safe" in t
    ):
        return "🟢", "AMAN"

    # kena blok
    if "blocked" in t or "diblokir" in t or "blocklist" in t:
        return "🔴", "TERBLOKIR"

    return "⚪", "STATUS TIDAK DIKETAHUI"


def check_domain(driver, domain):
    driver.get("https://nawalacheck.skiddle.id/")
    sleep(3)  # tunggu halaman siap

    # textarea input domain: <textarea id="domains" name="domains" ...>
    input_box = driver.find_element(By.CSS_SELECTOR, "#domains")
    input_box.clear()
    input_box.send_keys(domain)

    # submit form (CTRL+ENTER di textarea)
    input_box.send_keys(Keys.CONTROL, Keys.ENTER)

    # tunggu hasil keluar
    sleep(5)

    # container hasil: <div id="results" class="mt-8"></div>
    result_el = driver.find_element(By.CSS_SELECTOR, "#results")
    status_text = result_el.text.strip()

    return status_text


def main():
    domains = load_domains()
    driver = setup_driver()

    for d in domains:
        try:
            status_text = check_domain(driver, d)
        except Exception as e:
            status_text = f"ERROR: {e}"

        emoji, label = classify_status_text(status_text)

        ts = datetime.now().isoformat(timespec="seconds")
        # PERHATIKAN: di sini ada emoji di depan
        line = f"{emoji} [{ts}] {d} -> {label}\n{status_text}"

        print(line, flush=True)
        send_telegram(line)

    driver.quit()


if __name__ == "__main__":
    main()
