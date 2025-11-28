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


def check_domain(driver, domain):
    driver.get("https://nawalacheck.skiddle.id/")
    sleep(3)  # tunggu halaman siap

    # ====== selector yang sudah disesuaikan ======
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
    status = result_el.text.strip()
    return status


def main():
    domains = load_domains()
    driver = setup_driver()

    for d in domains:
        try:
            status = check_domain(driver, d)
        except Exception as e:
            status = f"ERROR: {e}"

        ts = datetime.now().isoformat(timespec="seconds")
        line = f"[{ts}] {d} -> {status}"

        # tampil di log Railway
        print(line, flush=True)

        # kirim juga ke Telegram
        send_telegram(line)

    driver.quit()


if __name__ == "__main__":
    main()
