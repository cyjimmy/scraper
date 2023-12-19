import re
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import json
from random import randint
from datetime import datetime
from selenium.webdriver.common.by import By
import csv
import os



class AutotraderMainBot:
    WEBSITE_NAME = "autotrader"
    RESULTS_FOLDER = 'scraped_data'
    LISTING_FILE_NAME = 'listings.csv'
    STARTING_PAGE = "https://www.autotrader.ca/cars/bc/?rcp=100&rcs=33800&srt=9&prx=-2&prv=British%20Columbia&loc=bc&hprc=True&wcp=True&sts=Used&inMarket=advancedSearch"
    USER_AGENT =  'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.53 Safari/537.36'
    SNAPSHOT_RESULTS_SELECTOR = '#result-item-inner-div'
    SNAPSHOT_NEXT_PAGE_SELECTOR = 'a.last-page-link'
    LISTING_SPECS_SELECTOR = "#sl-card-body"
    LISTING_WRAPPER_SELECTOR = "wrapper"
    LISTING_JS_SELECTOR = './/script[@type="text/javascript"]'
    SNAPSHOT_FIELDS = {
            'price': ('.price-amount', 'text'),
            'title': ('.h2-title .result-title .title-with-trim', 'text'),
            'num_photos': ('.photo-count', 'text', 'strip'),
            'photo_url': ('.main-photo img', 'data-original'),
            'location': ('.proximity .proximity-text.overflow-ellipsis', 'text'),
            'mileage': ('.odometer-proximity', 'text'),
            'description': ('.details', 'text'),
            'listing_url': ('.inner-link', 'href'),
            'dealer_name': ('div.seller-name', 'text')
        }
    
    def __init__(self, user_agent=USER_AGENT):
        # initialize options
        options = webdriver.ChromeOptions()
        options.add_argument("start-maximized")
        options.add_argument('--disable-blink-features=AutomationControlled')
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option('useAutomationExtension', False)
        options.add_experimental_option(
            "prefs", {
                "profile.managed_default_content_settings.images": 2,
            }
        )
        
        # initialize driver
        driver = webdriver.Chrome(options=options)
        driver.execute_cdp_cmd('Network.setUserAgentOverride', {"userAgent": user_agent})
        self.driver = driver
    
    @classmethod
    def create_filename(cls):
        current_time = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
        return f"./{cls.RESULTS_FOLDER}/{cls.WEBSITE_NAME}_{current_time}.csv"
    
    @staticmethod
    def output_snapshot_csv(filename, data):
        # Check and create directory if it doesn't exist
        directory = os.path.dirname(filename)
        if not os.path.exists(directory):
            os.makedirs(directory)

        file_exists = os.path.isfile(filename)
        
        with open(filename, 'a', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=AutotraderMainBot.SNAPSHOT_FIELDS.keys())
            
            if not file_exists:
                writer.writeheader()  # Write header only once
                
            writer.writerows(data)

    @staticmethod
    def output_listing_csv(data):
        root_dir = os.path.dirname(os.path.abspath(__file__))
        directory = os.path.join(root_dir, '..', AutotraderMainBot.RESULTS_FOLDER)
        if not os.path.exists(directory):
            os.makedirs(directory)
        output_path = os.path.join(directory, AutotraderMainBot.LISTING_FILE_NAME)
        file_exists = os.path.isfile(output_path)

        with open(output_path, 'a', newline='') as csvfile:
            print("Writing to file")
            fieldnames = data.keys()
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

            if not file_exists:
                writer.writeheader()

            writer.writerow(data)
    
    @classmethod
    def extract_snapshot_info(cls, main_div):
        car_info = {}
        for key, (selector, attribute, *extras) in cls.SNAPSHOT_FIELDS.items():
            try:
                element = main_div.find_element(By.CSS_SELECTOR, selector)
                value = element.text if attribute == 'text' else element.get_attribute(attribute)
                if extras and extras[0] == 'strip':
                    value = value.strip()
                car_info[key] = value
            except:
                car_info[key] = None
                
        return car_info
            
    def run(self, pages=None):
        self.driver.get(self.STARTING_PAGE)

        time.sleep(2)

        filename = self.create_filename()
        
        page = 0
        while True:
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_all_elements_located((By.CSS_SELECTOR, self.SNAPSHOT_RESULTS_SELECTOR))
            )

            main_divs = self.driver.find_elements(By.CSS_SELECTOR, self.SNAPSHOT_RESULTS_SELECTOR)

            page_car_info = []
            for main_div in main_divs:
                page_car_info.append(self.extract_snapshot_info(main_div))

            self.output_snapshot_csv(filename, page_car_info)
            
            if pages and page >= pages:
                break

            try:
                WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, self.SNAPSHOT_NEXT_PAGE_SELECTOR))
                )
                next_link = self.driver.find_element(By.CSS_SELECTOR, self.SNAPSHOT_NEXT_PAGE_SELECTOR)
                self.driver.execute_script("arguments[0].scrollIntoView();", next_link)
                print("Clicking next link")
                page += 1
                next_link.click()
            except Exception as e:
                print(e)
                print("No more pages")
                break

        self.driver.quit()
        
    def test(self):
        self.driver.get(self.STARTING_PAGE)

        # time.sleep(2)

        filename = self.create_filename()
        
        page = 1
        while True:
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_all_elements_located((By.CSS_SELECTOR, self.SNAPSHOT_RESULTS_SELECTOR))
            )

            main_divs = self.driver.find_elements(By.CSS_SELECTOR, self.SNAPSHOT_RESULTS_SELECTOR)

            page_car_info = []
            for main_div in main_divs:
                page_car_info.append(self.extract_snapshot_info(main_div))

            # self.driver.get(page_car_info[0]['listing_url'])
            
            with open('sample_listing_source.html', 'w') as f:
                f.write(self.driver.page_source)
            
            # time.sleep(50)
            break
            
            # self.append_to_file(filename, page_car_info)
            
            

            # try:
            #     WebDriverWait(self.driver, 10).until(
            #         EC.presence_of_element_located((By.CSS_SELECTOR, self.NEXT_PAGE_CSS_SELECTOR))
            #     )
            #     next_link = self.driver.find_element(By.CSS_SELECTOR, self.NEXT_PAGE_CSS_SELECTOR)
            #     self.driver.execute_script("arguments[0].scrollIntoView();", next_link)
            #     print("Clicking next link")
            #     page += 1
            #     next_link.click()
            # except Exception as e:
            #     print(e)
            #     print("No more pages")
            #     break

        self.driver.quit()

    def extract_listing_info(self, url=None):
        if not url:
            url = "https://www.autotrader.ca/a/toyota/tundra/vernon/british%20columbia/19_12736412_/?showcpo=ShowCpo&ncse=no&ursrc=pl&urp=5&urm=8&sprx=-2"

        specs_dict = {}

        self.driver.get(url)
        WebDriverWait(self.driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, self.LISTING_SPECS_SELECTOR))
        )

        specs_div = self.driver.find_element(By.CSS_SELECTOR, self.LISTING_SPECS_SELECTOR)
        specs_div_content = specs_div.get_attribute('outerHTML')
        specs_list = BeautifulSoup(specs_div_content, 'html.parser')

        for index, li in enumerate(specs_list.find_all('li', {'class': 'list-item'})):
            key = li.find('span', {'id': f'spec-key-{index}'}).text.strip()
            specs_dict[key] = li.find('span', {'id': f'spec-value-{index}'}).text.strip()

        wrapper = self.driver.find_element(By.ID, self.LISTING_WRAPPER_SELECTOR)
        script = wrapper.find_elements(By.XPATH, self.LISTING_JS_SELECTOR)[1]
        script_content = script.get_attribute('innerHTML')
        vin_match = re.search(r'"vin":"([^"]*)"', script_content)
        specs_dict["VIN"] = vin_match.group(1) if vin_match else None
        return specs_dict

        

def main():
    bot = AutotraderMainBot()
    bot.run(pages = 2)
    # bot.extract_listing_info()


if __name__ == "__main__":
    main()
