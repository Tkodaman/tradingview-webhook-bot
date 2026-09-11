from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import time

options = Options()
options.add_argument('--headless')
options.set_window_size(1920, 1080)

driver = webdriver.Chrome(options=options)
driver.get("http://127.0.0.1:8000")
time.sleep(3)
driver.save_screenshot("screenshot_final_fixed.png")
driver.quit()
