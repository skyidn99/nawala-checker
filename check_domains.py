import os
import requests

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from time import sleep

DOMAINS_FILE = "domains.txt"

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")


def send_telegram(text: str):
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
    with open(DOMAINS_FILE) as f:
        return [line.strip() for line in f if line.strip()]


def check_single_domain(driver, domain: str) -> str:
    driver.get("https://nawalacheck.skiddle.id/")
    sleep(3)

    # textarea id="domains"
    input_box = driver.find_element(By.CSS_SELECTOR, "#domains")
    input_box.clear()
    input_box.send_keys(domain)
    input_box.send_keys(Keys.CONTROL, Keys.ENTER)

    # kasih waktu JS loading agak lama
    sleep(8)

    result_el = driver.find_element(By.CSS_SELECTOR, "#results")
    # pakai innerText supaya semua anak <p>/<li> ikut kebaca
    status_text = result_el.get_attribute("innerText") or ""
    status_text = status_text.strip()

    return status_text


def main():
    print("=== DEBUG RAW MODE ===", flush=True)

    domains = load_domains()
    driver = setup_driver()

    lines = ["Domain Status Report (RAW dari nawalacheck.skiddle.id)"]

    for d in domains:
        try:
            status_text = check_single_domain(driver, d)
        except Exception as e:
            status_text = f"ERROR: {e}"

        line = f"{d} -> {status_text}"
        print(line, flush=True)
        lines.append(line)

    driver.quit()

    message = "\n".join(lines)
    send_telegram(message)


if __name__ == "__main__":
    main()
