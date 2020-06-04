import os
from telnetlib import EC
from time import sleep
import pandas as pd
from selenium.common.exceptions import TimeoutException
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait
from src.utils import get_full_path


options = Options()
options.add_argument("start-maximized")
options.add_argument("--disable-extensions")
options.add_argument('--headless')
options.add_argument('window-size=1920x1080')
options.add_argument('--no-sandbox')
options.add_argument("--hide-scrollbars")
options.add_argument("disable-infobars")
options.add_argument('--disable-dev-shm-usage')
prefs = {
    "translate_whitelists": {"fr": "en", "de": "en", 'it': 'en', 'no': 'en', 'es': 'en', 'sv': 'en', 'nl': 'en',
                             'da': 'en', 'pl': 'en', 'fi': 'en', 'cs': 'en'},
    "translate": {"enabled": "true"}
}
options.add_experimental_option("prefs", prefs)


class ProductLinksGetter:
    def __init__(self):
        self.web_url = 'https://aliexpress.com/category/70805/mice.html?categoryName=Mice&spm=a2g0n.category-amp.leafcat.Mice'
        self.pro_links_list = []
        self.limit=30
        self.driver = webdriver.Chrome(options=options)

    def start(self):
        print('start')
        self.get_pro_links()

    def set_cookies(self):
        try:
            sleep(5)
            self.driver.implicitly_wait(10)
            cookie = {'name': 'foo', 'value': 'bar'}
            self.driver.add_cookie(cookie)
            element = self.driver.find_element_by_xpath('//*[@id="CybotCookiebotDialogBodyButtonAccept"]')
            self.driver.execute_script("arguments[0].click();", element)
            print(f"Cookies set ==> {cookie}")
        except Exception as error:
            print(f"Failed in setting cookies ==> {error}")

    def get_link_onpage(self):
        product_raw = self.driver.find_elements_by_css_selector('li.list-item')
        print(f'Lent of raw products: {len(product_raw)}')
        for product in product_raw:
            try:
                product_source_code = product.get_attribute("innerHTML")
                product_soup: BeautifulSoup = BeautifulSoup(product_source_code, 'html.parser')
                a_tag = product_soup.find('a')
                source_url =f"https:{a_tag.get('href')}"
                print()
                print(f"This append ==>{source_url}")
                self.pro_links_list.append(source_url)
            except Exception as error:
                print(f"Error in extracting source ==> {error}")

        print(len(self.pro_links_list))
        print(f"Length Before ==> {len(self.pro_links_list)}")
        rd_pro_links_list = list(dict.fromkeys(self.pro_links_list))
        print(f"Length After ==> {len(rd_pro_links_list)}")
        os.makedirs(get_full_path("../data/"), exist_ok=True)
        pd.DataFrame(rd_pro_links_list).to_json(get_full_path("../data/links_pd.json"))

    def remove_popup_banner(self):
        try:
            self.driver.implicitly_wait(10)
            WebDriverWait(self.driver, 20).until(EC.element_to_be_clickable(
                (By.CSS_SELECTOR, 'a.next-dialog-close'))).click()
            print('==> Clicked and remove popup banner')
            self.driver.implicitly_wait(5)
            self.driver.execute_script("window.scrollTo(0, 200)")
            sleep(5)
        except Exception as e:
            print('Error in clicking popup banner BTN : ' + str(e))

    def click_on_button(self, click_div):
        xpath = f'//*[@id="outer-result-main"]/div[1]/div/ul/li[{click_div}]/a'
        try:
            element = self.driver.find_element_by_xpath(xpath)
            self.driver.execute_script("arguments[0].click();", element)
            sleep(5)
        except Exception as e:
            print(f'Error in clicking this path {xpath} BTN : ' + str(e))
        sleep(1)

    def click_on_next_btn(self):
        try:
            element = self.driver.find_element_by_css_selector('div.next-pagination-list+button.next-btn')
            self.driver.execute_script("arguments[0].click();", element)
            sleep(5)
        except Exception as e:
            print(f'Error in clicking Next page BTN =>' + str(e))
        sleep(2)

    def login(self):
        try:
            # Need to enter user email here
            # user='example1@gmail.com'
            user='mobinalhassan1@gmail.com'
            # Need to enter user password here
            # password='example1234'
            password='mobin12566465'
            user_input = self.driver.find_element_by_css_selector('#fm-login-id')
            password_input = self.driver.find_element_by_css_selector('#fm-login-password')
            user_input.send_keys(user)
            sleep(2)
            password_input.send_keys(password)
            sleep(2)
            btn=self.driver.find_element_by_css_selector('button')
            sleep(2)
            btn.click()
        except Exception:
            print(f'User login not require!')

    def w8_until_loading(self):
        try:
            delay=15
            WebDriverWait(self.driver, delay).until(EC.presence_of_element_located((By.CSS_SELECTOR, 'li.list-item')))
            print('Page is ready!')
        except TimeoutException:
            print('Loading took too much time!')

    def infinatescroll(self):
        sleep(1)
        try:
            sleep(2)
            self.driver.execute_script("window.scrollTo(0, 1000)")
            pre=1000
            for i in range(0,20):
                sleep(1)
                nextscr = pre + 1000
                pre = pre + 1000
                self.driver.execute_script(f"window.scrollTo({pre}, {nextscr});")
                print('Scrolling Down...')
                # Wait to load page
                sleep(1)
        except Exception as e:
            print('Error in scrolling : ' + str(e))

    def get_pro_links(self):
        try:
            print(self.web_url)
            self.driver.get(self.web_url)
            sleep(5)
            self.login()
            sleep(3)
            self.remove_popup_banner()
            self.w8_until_loading()
            sleep(3)
            self.infinatescroll()
            self.get_link_onpage()
            # for i in range(1, 60):
            for i in range(1, 2):
                self.click_on_next_btn()
                self.w8_until_loading()
                self.infinatescroll()
                self.get_link_onpage()
            self.driver.quit()
        except Exception as error:
            print(f'Quitting form get pro link function ==> {error}')
            self.driver.quit()


def main():
    pro_link_getter = ProductLinksGetter()
    pro_link_getter.start()


if __name__ == "__main__":
    main()
