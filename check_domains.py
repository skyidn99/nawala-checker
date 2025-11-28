import os
import requests

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from time import sleep

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")
DOMAINS_ENV = os.environ.get("DOMAINS_TO_CHECK", "")


def send_telegram(text: str):
    """Kirim pesan ke Telegram."""
    if not TELEGRAM_TOKEN or not TELEGRAM_CHAT_ID:
        print("Telegram env belum di-set")
        return

    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": text,
        "disable_web_page_preview": True,
    }
    try:
        resp = requests.post(url, json=payload, timeout=10)
        print("Telegram resp:", resp.status_code, resp.text[:200])
    except Exception as e:
        print("Gagal kirim ke Telegram:", e)


def setup_driver():
    options = Options()
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    driver = webdriver.Chrome(options=options)
    return driver


def load_domains():
    """
    Ambil daftar domain dari env DOMAINS_TO_CHECK.
    Format: dipisah dengan koma, boleh pakai enter.

    Contoh di Railway Variables:

    DOMAINS_TO_CHECK = pemburuscatter.com, che-la.lol, boxing55ab.store,
                       boxing55ai.store, boxing55we.site
    """
    if not DOMAINS_ENV:
        print("DOMAINS_TO_CHECK kosong, tidak ada domain untuk dicek.", flush=True)
        return []

    raw = DOMAINS_ENV.replace("\n", ",")
    parts = [p.strip() for p in raw.split(",")]
    domains = [p for p in parts if p]
    print("Loaded domains from DOMAINS_TO_CHECK:", domains, flush=True)
    return domains


def classify_status_text(status_text: str):
    """
    Ubah teks hasil dari Nawala menjadi emoji + label singkat.
    """
    t = status_text.lower().strip()

    if not t:
        return "⚪", "Unknown"

    if "not blocked" in t or "tidak diblokir" in t or "clean" in t or "safe" in t:
        return "🟢", "Not Blocked"

    if "blocked" in t or "diblokir" in t or "blocklist" in t:
        return "🔴", "Blocked"

    return "⚪", "Unknown"


def check_single_domain(driver, domain: str) -> str:
    """
    Buka halaman, isi domain, KLIK tombol 'Check Domains', lalu baca hasil.
    """
    driver.get("https://nawalacheck.skiddle.id/")
    sleep(3)

    # textarea domain (biasanya cuma satu di halaman)
    textarea = driver.find_element(By.TAG_NAME, "textarea")
    textarea.clear()
    textarea.send_keys(domain)

    # klik tombol yang mengandung teks 'Check Domains'
    button = driver.find_element(By.XPATH, "//button[contains(., 'Check Domains')]")
    button.click()

    # tunggu JS memproses
    sleep(8)

    result_el = driver.find_element(By.CSS_SELECTOR, "#results")
    status_text = (result_el.get_attribute("innerText") or "").strip()
    return status_text


def main():
    print("=== DOMAIN CHECKER (ENV ONLY) ===", flush=True)

    domains = load_domains()
    if not domains:
        send_telegram("Domain Status Report\nTidak ada domain untuk dicek.")
        return

    driver = setup_driver()

    lines = ["Domain Status Report"]

    for d in domains:
        try:
            status_text = check_single_domain(driver, d)
            emoji, label = classify_status_text(status_text)
        except Exception as e:
            status_text = f"ERROR: {e}"
            emoji, label = "⚪", "ERROR"

        line = f"{d}: {emoji} {label}"
        print(line, flush=True)
        lines.append(line)

    driver.quit()

    message = "\n".join(lines)
    send_telegram(message)


if __name__ == "__main__":
    main()
