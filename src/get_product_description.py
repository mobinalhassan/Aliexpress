import re
import threading
import pandas as pd
from time import sleep
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.remote.webelement import WebElement
from src.utils import get_full_path
from src.model import aliexpress
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from src.user_agents import user_agents
import random

pro_links_list = pd.read_json(get_full_path('../data/links_pd.json'))
pro_links_list = pro_links_list[0].tolist()
print(f"Length of products link ==> {len(pro_links_list)}")


class ProductDescriptionGetter:
    products_list = []

    def __init__(self, link):
        self.pro_url = link
        self.product = aliexpress.copy()
        self.product['source'] = self.pro_url
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
        useragent = random.choice(user_agents)
        print(f'User Agent ==> {useragent}')
        options.add_argument(f'user-agent={useragent}')
        self.driver = webdriver.Chrome(options=options)

    def __del__(self):
        print("Delete")

    def start(self):
        print('Start')
        self.get_pro_desc()

    def save_csv_file(self):
        self.products_list.append(self.product.copy())
        dataframe = pd.DataFrame(self.products_list)
        dataframe.to_csv(get_full_path("../data/dataset.csv"), index=False)
        # dataframe.to_json(get_full_path("../data/dataset.json"), orient='records')
        print(f'File saved! Records ==> {len(self.products_list)}')

    def get_pro_title(self):
        try:
            title_pro: WebElement = self.driver.find_element_by_css_selector('div[itemprop="name"]').text
            title_pro_str = str(str(title_pro).strip())
            self.product['product_name'] = title_pro_str
            print(f"Product title ==> {title_pro_str}")
        except Exception as error:
            print(f"Error! in getting pro Title ==> {error}")

    def get_pro_price(self):
        try:
            price: WebElement = self.driver.find_element_by_css_selector('span[itemprop="price"]').text
            print(f"Product price ==> {price}")
            # self.product['price'] = price
            return price
        except Exception as error:
            print(f"Error! in getting Price and currency {error}")

    def get_pro_description(self):
        try:
            description: WebElement = self.driver.find_element_by_css_selector('div#product-description')
            description_source_code = description.get_attribute("innerHTML")
            description_soup: BeautifulSoup = BeautifulSoup(description_source_code, 'html.parser')
            description_f = str(description_soup.get_text(' ')).encode('ascii', 'ignore').decode('utf-8')
            description_f = str(description_f.strip().replace('\n', ' ').replace('   ', ' ').replace('  ', ' '))
            check = re.split(r'=|%2F|%20|&|,|\t| {3}| {4}|;|:|/|\?', str(description_f).strip().lower())
            joined = ' '.join(check)
            self.product['description'] = joined.strip()
            print(f"Product description ==> {joined}")
        except Exception as error:
            print(f"Error! in getting Description {error}")

    def get_pro_photos(self):
        other_pic_list = []
        try:
            product_gallery = self.driver.find_element_by_css_selector('ul.images-view-list')
            product_gallery_source_code = product_gallery.get_attribute("innerHTML")
            product_gallery_soup: BeautifulSoup = BeautifulSoup(product_gallery_source_code, 'html.parser')
            for i, pro_link_for in enumerate(product_gallery_soup.findAll('img')):
                try:
                    other_pic = pro_link_for['src']
                    single_pic = f"{other_pic.split('.jpg')[0]}.jpg"
                    other_pic_list.append(single_pic)
                except KeyError as error:
                    print(error)

            try:
                product_descp = self.driver.find_element_by_css_selector('div#product-description')
                product_descp_source_code = product_descp.get_attribute("innerHTML")
                product_descp_soup: BeautifulSoup = BeautifulSoup(product_descp_source_code, 'html.parser')
                for pro_link_for in product_descp_soup.findAll('img'):
                    try:
                        single_pic = pro_link_for["src"]
                        other_pic_list.append(single_pic)
                    except KeyError as error:
                        print(error)
            except Exception as error:
                print(f"Error! in getting Photos in  Description {error}")

            rd_other_pic_list = list(dict.fromkeys(other_pic_list))
            for i, photo in enumerate(rd_other_pic_list):
                print(f"Product Photo ==> {photo}")
                self.product[f'IM{i + 1}'] = None
                self.product[f'IM{i + 1}'] = photo

        except Exception as error:
            print(f"Error! in getting Photos list {error}")

    def get_pro_quantity(self):
        try:
            quantity: WebElement = self.driver.find_element_by_css_selector('div.product-quantity-tip span').text
            print(f"Product Quantity ==> {str(quantity).split()[0]}")
            return str(quantity).split()[0]
        except Exception as error:
            print(f"Error! in getting brand ==> {error}")
            self.driver.quit()

    def get_pro_sku(self):
        try:
            sku = str(self.pro_url).split('.html')[0].split('/')[-1]
            self.product['sku'] = sku
            print(f'Product SKU ==> {sku}')
        except Exception as e:
            print(f'Product SKU not found => {e}')

    def remove_popup_banner(self):
        try:
            self.driver.implicitly_wait(10)
            WebDriverWait(self.driver, 20).until(EC.element_to_be_clickable(
                (By.CSS_SELECTOR, 'a.next-dialog-close'))).click()
            print('==> Clicked and remove popup banner')
            self.driver.implicitly_wait(5)
            self.driver.execute_script("window.scrollTo(0, 200)")
            sleep(1)
        except Exception as e:
            print('Error in clicking popup banner BTN : ' + str(e))

    def infinatescroll(self):
        try:
            sleep(2)
            self.driver.execute_script("window.scrollTo(0, 1000)")
            pre = 1000
            for i in range(0, 6):
                sleep(1)
                nextscr = pre + 1000
                pre = pre + 1000
                self.driver.execute_script(f"window.scrollTo({pre}, {nextscr});")
                print('Scrolling Down...')
                # Wait to load page
                sleep(1)
        except Exception as e:
            print('Error in scrolling : ' + str(e))

    def get_pro_reviews(self):
        try:
            self.driver.execute_script("window.scrollTo(0, 200)")
            self.driver.implicitly_wait(10)
            WebDriverWait(self.driver, 20).until(EC.element_to_be_clickable(
                (By.XPATH, '/html/body/div[5]/div/div[3]/div[2]/div[2]/div[1]/div/div[1]/ul/li[2]'))).click()
            print('==> Review tab Clicked')
            self.driver.implicitly_wait(5)
            self.driver.execute_script("window.scrollTo(200, 1200)")
        except Exception as error:
            print(f'Error in Clicking review tab ==>{error}')
        try:
            sleep(5)
            che = WebDriverWait(self.driver, 10).until(EC.frame_to_be_available_and_switch_to_it(
                self.driver.find_element_by_xpath("//*[@id='product-evaluation']")))
            print(f'==> Swithched to iframe {che}')
            print()
            sleep(3)
            review_elem_source_code = self.driver.execute_script("return document.body.innerHTML;")
            review_elem_soup: BeautifulSoup = BeautifulSoup(review_elem_source_code, 'html.parser')
            for i, review_raw in enumerate(review_elem_soup.select('div.feedback-item')):
                print('*' * 100)
                review = str(review_raw.select_one('dt.buyer-feedback > span').get_text()).encode('ascii',
                                                                                                  'ignore').decode(
                    'utf-8').strip()
                print(f'Review {i + 1} ==> {review}')
                self.product[f'review{i + 1}'] = None
                self.product[f'review{i + 1}'] = review
                if i >= 9:
                    break
                print('*' * 100)
            self.driver.switch_to.default_content()
        except Exception as error:
            self.product['Review'] = 'Reviews Not available'
            print(f'Error in getting Reviews ==>{error}')

    def get_varients(self):

        varients_list = self.driver.find_elements_by_css_selector('div.sku-property')
        if len(varients_list) > 1:
            check1 = str(varients_list[0].find_element_by_css_selector('div.sku-title').text).find('Ship')
            check2 = str(varients_list[1].find_element_by_css_selector('div.sku-title').text).find('Color')
            if check1 != -1 and check2 != -1:
                print('Method 1: Shipping and Color')
                self.m1(index1=0, index2=1)
                return None

            check1 = str(varients_list[0].find_element_by_css_selector('div.sku-title').text).find('Color')
            check2 = str(varients_list[1].find_element_by_css_selector('div.sku-title').text).find('Ship')
            if check1 != -1 and check2 != -1:
                print('Method 2: Color and Shipping')
                self.m1(index1=1, index2=0)
                return None

        print('Other Method')

        try:
            li_list = self.driver.find_elements_by_css_selector('ul.sku-property-list')[0]
            sleep(1)
            if len(li_list.find_elements_by_css_selector('li.sku-property-item')) > 1:
                # for i, li_click in enumerate(li_list.find_elements_by_css_selector('li.sku-property-item')[1:]):
                for i, li_click in enumerate(li_list.find_elements_by_css_selector('li.sku-property-item')):
                    try:
                        li_click.click()
                    except:
                        continue
                    try:
                        self.varent_product = self.product.copy()
                        self.varent_product['price'] = None
                        self.varent_product['variation'] = f'variation{i + 1}'
                        try:
                            variation_photo_source_code = li_click.get_attribute("innerHTML")
                            product_gallery_soup: BeautifulSoup = BeautifulSoup(variation_photo_source_code,
                                                                                'html.parser')
                            for i, pro_link_for in enumerate(product_gallery_soup.findAll('img')):
                                try:
                                    self.varent_product['variation_photo'] = None
                                    other_pic = pro_link_for['src']
                                    single_pic = f"{other_pic.split('.jpg')[0]}.jpg"
                                    self.varent_product['variation_photo'] = single_pic
                                except KeyError as error:
                                    print(error)
                        except Exception as error:
                            print(f"Error! in variation photo ==> {error}")

                        try:
                            self.varent_product['quantity'] = None
                            self.varent_product['quantity'] = self.get_pro_quantity()
                        except Exception as error:
                            print(f"Error! in getting brand ==> {error}")
                        self.varent_product['price'] = self.get_pro_price()
                        self.products_list.append(self.varent_product.copy())
                    except Exception as error:
                        print(f"Error! in getting Price and currency {error}")
        except Exception as e:
            print('Error in clicking popup banner BTN : ' + str(e))

    def m1(self, index1, index2):
        shipping_list = self.driver.find_elements_by_css_selector('ul.sku-property-list')[
            int(index1)].find_elements_by_css_selector('li.sku-property-item')
        for ship in shipping_list:
            try:
                ship.click()
            except:
                continue
            ship_from = str(ship.text).strip()
            print(ship_from)
            color_type_list = self.driver.find_elements_by_css_selector('ul.sku-property-list')[
                int(index2)].find_elements_by_css_selector('li.sku-property-item')
            for i, li_click in enumerate(color_type_list):
                try:
                    li_click.click()
                except:
                    continue
                try:
                    pro_single = self.product.copy()
                    pro_single['price'] = None
                    pro_single['price'] = self.get_pro_price()
                    pro_single['quantity'] = None
                    pro_single['quantity'] = self.get_pro_quantity()
                    pro_single['Ship_From'] = ship_from
                    pro_single['variation'] = f'variation{i + 1}'
                    try:
                        # product_gallery = self.driver.find_element_by_css_selector('ul.images-view-list')
                        variation_photo_source_code = li_click.get_attribute("innerHTML")
                        product_gallery_soup: BeautifulSoup = BeautifulSoup(variation_photo_source_code,
                                                                            'html.parser')
                        for i, pro_link_for in enumerate(product_gallery_soup.findAll('img')):
                            try:
                                pro_single['variation_photo'] = None
                                other_pic = pro_link_for['src']
                                single_pic = f"{other_pic.split('.jpg')[0]}.jpg"
                                pro_single['variation_photo'] = single_pic
                            except KeyError as error:
                                print(error)
                    except Exception as error:
                        print(f"Error! in variation photo ==> {error}")
                    self.products_list.append(pro_single.copy())
                    # color_type_list[0].click()
                except Exception as error:
                    print(f"Error! in getting Price and currency {error}")
                sleep(1)
    def get_pro_desc(self):
        try:
            print(f"Getting Desc for URL ==> {self.pro_url}")
            self.driver.get(self.pro_url)
            sleep(5)
            self.product['price'] = self.get_pro_price()
            self.product['quantity'] = self.get_pro_quantity()
            self.get_pro_title()
            self.get_pro_sku()
            self.remove_popup_banner()
            self.infinatescroll()
            self.get_pro_description()
            self.get_pro_reviews()
            self.get_pro_photos()
            self.get_varients()
            self.save_csv_file()
            print(self.product)
            print('*' * 150)
            self.driver.quit()
        except Exception as error:
            print(f"Error in getting desctiption page ==> {error}")


thread = 1


def main():
    for i in range(0, len(pro_links_list), thread):
        all_t = []
        twenty_records = pro_links_list[i:i + thread]
        for record_arg in twenty_records:
            try:
                pdg = ProductDescriptionGetter(record_arg)
                t = threading.Thread(target=pdg.start)
                t.start()
                all_t.append(t)
            except Exception as error:
                print(f"Error in starting thread ==> {error}")
        for count, t in enumerate(all_t):
            print(f" joining Thread no ==> {count}")
            t.join()


if __name__ == "__main__":
    main()
