from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import time

options = Options()
options.add_argument('--headless')
options.set_capability('goog:loggingPrefs', {'browser': 'ALL'})

driver = webdriver.Chrome(options=options)
driver.get("http://127.0.0.1:8000")
time.sleep(3)

logs = driver.get_log('browser')
for log in logs:
    if log['level'] in ['SEVERE', 'WARNING', 'ERROR']:
        print(f"[{log['level']}] {log['message']}")

driver.quit()
