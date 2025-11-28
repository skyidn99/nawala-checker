from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from time import sleep
from datetime import datetime

DOMAINS_FILE = "domains.txt"

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

    # ====== PENTING: selector yang sudah disesuaikan ======
    # textarea input domain: <textarea id="domains" name="domains" ...>
    input_box = driver.find_element(By.CSS_SELECTOR, "#domains")
    input_box.clear()
    input_box.send_keys(domain)

    # submit form (klik Enter di textarea atau bisa juga cari tombol submit)
    input_box.send_keys(Keys.CONTROL, Keys.ENTER)  # kalau tidak jalan, ganti dengan klik tombol

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
        print(f"[{ts}] {d} -> {status}", flush=True)

    driver.quit()

if __name__ == "__main__":
    main()
