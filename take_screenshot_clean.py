from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
import time

options = Options()
options.add_argument('--headless')
driver = webdriver.Chrome(options=options)

try:
    driver.get("http://localhost:8000")
    time.sleep(3) # Wait for JS to execute
    driver.save_screenshot("screenshot.png")
    print("Saved screenshot.png")
except Exception as e:
    print("Error:", e)
finally:
    driver.quit()
