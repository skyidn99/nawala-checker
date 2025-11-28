import os
import requests

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from time import sleep

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
        "disable_web_page_preview": True,
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
    Sesuaikan kata-kata di sini kalau nanti teks-nya berbeda.
    """
    t = status_text.lower().strip()

    if not t:
        return "⚪", "Unknown"

    if "not blocked" in t or "tidak diblokir" in t:
        return "🟢", "Aman"

    if "blocked" in t or "diblokir" in t or "blocklist" in t:
        return "🔴", "Blocked"

    return "⚪", "Unknown"


def check_single_domain(driver, domain: str) -> str:
    """
    Membuka halaman nawalacheck, cek satu domain,
    dan mengembalikan teks penuh dari <div id="results">.
    """
    driver.get("https://nawalacheck.skiddle.id/")
    sleep(3)

    # textarea: <textarea id="domains" name="domains" ...>
    input_box = driver.find_element(By.CSS_SELECTOR, "#domains")
    input_box.clear()
    input_box.send_keys(domain)

    # submit form
    input_box.send_keys(Keys.CONTROL, Keys.ENTER)

    sleep(5)

    result_el = driver.find_element(By.CSS_SELECTOR, "#results")
    return result_el.text.strip()


def main():
    print("=== NEW VERSION: GROUPED REPORT ===", flush=True)

    domains = load_domains()
    driver = setup_driver()

    lines = ["Domain Status Report"]

    for d in domains:
        try:
            status_text = check_single_domain(driver, d)
            emoji, label = classify_status_text(status_text)
        except Exception as e:
            emoji, label = "⚪", f"ERROR: {e}"

        line = f"{d}: {emoji} {label}"
        print(line, flush=True)
        lines.append(line)

    driver.quit()

    # Gabungkan jadi satu pesan ke Telegram
    message = "\n".join(lines)
    print("=== SENDING TELEGRAM MESSAGE ===")
    print(message)
    send_telegram(message)


if __name__ == "__main__":
    main()
