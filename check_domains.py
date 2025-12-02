import os
import requests

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
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
        "parse_mode": "HTML",
    }
    try:
        resp = requests.post(url, json=payload, timeout=15)
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
    Format: bisa dipisah koma atau enter.

    Contoh di Railway Variables:

    DOMAINS_TO_CHECK = alien55.com, alien55.site, alien55.vip
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
    Ubah teks hasil dari tabel Nawala menjadi emoji + label singkat.
    """
    t = (status_text or "").strip().lower()

    if not t:
        return "⚪", "Unknown"

    # penting: cek "not blocked" dulu supaya tidak ketimpa kata "blocked"
    if "not blocked" in t or "tidak diblokir" in t:
        return "🟢", "Not Blocked"

    if "blocked" in t or "diblokir" in t or "blocklist" in t:
        return "🔴", "Blocked"

    if "error" in t:
        return "🟠", "Error"

    return "⚪", status_text.strip() or "Unknown"


def check_single_domain(driver, domain: str) -> str:
    """
    Buka halaman, isi SATU domain di textarea, klik 'Check Domains',
    lalu baca teks status domain tersebut dari tabel (kolom Status).
    """
    driver.get("https://nawalacheck.skiddle.id/")
    sleep(2)

    # textarea domain (hanya satu di halaman)
    textarea = driver.find_element(By.TAG_NAME, "textarea")
    textarea.clear()
    textarea.send_keys(domain)

    # klik tombol "Check Domains"
    button = driver.find_element(By.XPATH, "//button[contains(., 'Check Domains')]")
    button.click()

    # tunggu sampai minimal satu baris hasil muncul di tabel
    WebDriverWait(driver, 60).until(
        EC.presence_of_element_located(
            (By.CSS_SELECTOR, "#results table tbody tr")
        )
    )

    rows = driver.find_elements(By.CSS_SELECTOR, "#results table tbody tr")
    status_text = ""

    for row in rows:
        tds = row.find_elements(By.TAG_NAME, "td")
        if len(tds) < 2:
            continue

        domain_cell = tds[0].text.strip().lower()
        status_cell = tds[1].text.strip()

        # seharusnya hanya 1 domain di tabel, tapi kita cocokan nama domain untuk aman
        if domain_cell == domain.lower():
            status_text = status_cell
            break

    # fallback: kalau tidak ketemu row yang cocok, ambil status baris pertama
    if not status_text and rows:
        first_tds = rows[0].find_elements(By.TAG_NAME, "td")
        if len(first_tds) >= 2:
            status_text = first_tds[1].text.strip()

    return status_text


def main():
    print("=== DOMAIN CHECKER (ENV ONLY) ===", flush=True)

    domains = load_domains()
    if not domains:
        send_telegram("Domain Status Report\nTidak ada domain untuk dicek.")
        return

    driver = setup_driver()

    lines = ["<b>Domain Status Report</b>"]

    for d in domains:
        try:
            status_text = check_single_domain(driver, d)
            emoji, label = classify_status_text(status_text)
        except Exception as e:
            status_text = f"ERROR: {e}"
            emoji, label = "⚪", "ERROR"

        line_plain = f"{d}: {emoji} {label}"
        print(line_plain, flush=True)

        # format link klik-able di Telegram
        link = f"<a href=\"http://{d}\">{d}</a>"
        line_for_telegram = f"{link}: {emoji} {label}"
        lines.append(line_for_telegram)

    driver.quit()

    message = "\n".join(lines)
    send_telegram(message)


if __name__ == "__main__":
    main()
