import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
import re

def main(url):
    try:
        options = Options()
        options.headless = True
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service = service, options = options)
        driver.implicitly_wait(15)
        driver.get(url)
        productID = driver.find_element(By.CLASS_NAME, 'product-detail-list-item.item-title-share-collect').text
        driver.quit()
        return re.sub(r'\D', '', productID)
    except:
        print('-1')

# 用來測試函數
if __name__ == "__main__":
    print(main('https://www.uniqlo.com/tw/zh_TW/product-detail.html?productCode=u0000000020259'))