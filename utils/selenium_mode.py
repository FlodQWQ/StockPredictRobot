import pyperclip
from selenium.webdriver import Keys
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium import webdriver
from selenium.webdriver.common.by import By


class SeleniumMode:
    def __init__(self):
        driver_path = './utils/chromedriver.exe'
        chrome_options = Options()
        # chrome_options.add_argument('--headless')
        chrome_options.add_argument("--window-size=200,150")
        # chrome_options.page_load_strategy = 'eager'
        chrome_options.add_argument(
            'user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) '
            'Chrome/91.0.4472.124 Safari/537.36')
        service = Service(driver_path)
        self.driver = webdriver.Chrome(service=service, options=chrome_options)
        self.driver.set_page_load_timeout(40)

    def get_content(self, url):
        self.driver.get(url)
        body = self.driver.find_element(By.TAG_NAME, 'body')
        body.send_keys(Keys.CONTROL + 'a')
        body.send_keys(Keys.CONTROL + 'c')
        html_content = pyperclip.paste()
        self.driver.close()
        # print(html_content + "\n")
        return html_content
