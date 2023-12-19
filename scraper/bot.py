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
    LISTING_BASIC_INFO_FIELDS = {
        "price": "original price",
        "make": "make",
        "model": "model",
        "year": "year", 
        "vin": "vin", 
        "dealerCoName": "dealer", 
    }
    LISTING_SPECS_FIELDS = ["Kilometres", "Status", "Trim", "Body Type", "Engine", "Cylinder", "Transmission", "Drivetrain", "Stock Number", "Exterior Colour", "Interior Colour", "Passengers", "Doors", "Fuel Type", "City Fuel Economy", "Hwy Fuel Economy"]
    
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
        filename = self.create_filename()
        page = 0

        while not pages or page < pages:
            snapshot_url = self.driver.current_url

            try:
                WebDriverWait(self.driver, 10).until(
                    EC.presence_of_all_elements_located((By.CSS_SELECTOR, self.SNAPSHOT_RESULTS_SELECTOR))
                )
            except:
                print("Failed to load page ", snapshot_url)
                break

            main_divs = self.driver.find_elements(By.CSS_SELECTOR, self.SNAPSHOT_RESULTS_SELECTOR)

            page_car_info = []
            for main_div in main_divs:
                page_car_info.append(self.extract_snapshot_info(main_div))

            self.output_snapshot_csv(filename, page_car_info)

            for listing in page_car_info:
                listing_url = listing['listing_url']
                if not listing_url:
                    continue
                # TODO: Check if listing already exists in database
                listing_exists = False
                if listing_exists:
                    # TODO: Get lowest listing price from database, if current listing price is lower, update lowest price
                    continue
                else:
                    listing_info = self.extract_listing_info(listing_url)
                    if listing_info:
                        self.output_listing_csv(listing_info)

            self.driver.get(snapshot_url)

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
            url = "https://www.autotrader.ca/a/volkswagen/atlas%20cross%20sport/kelowna/british%20columbia/5_54065092_ct2004120103526706/?showcpo=ShowCpo&ncse=no&ursrc=hl&orup=34000_100_34162&sprx=-2,Turner"
        
        info_dict = {}
        info_dict['url'] = url

        try:
            self.driver.get(url)
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, self.LISTING_SPECS_SELECTOR))
            )
        except Exception as e:
            print("Failed to load listing page ", url)
            return None
        
        # Extract basic info
        try:
            wrapper = self.driver.find_element(By.ID, self.LISTING_WRAPPER_SELECTOR)
            script = wrapper.find_elements(By.XPATH, self.LISTING_JS_SELECTOR)[1]
            script_content = script.get_attribute('innerHTML')
            adBasicInfo_match = re.search(r'"adBasicInfo":\s*({.*?})', script_content)
            adBasicInfo = adBasicInfo_match.group(1) if adBasicInfo_match else None
            adBasicInfo = json.loads(adBasicInfo)
            for key, value in self.LISTING_BASIC_INFO_FIELDS.items():
                info_dict[value] = adBasicInfo.get(key, None)
                if key == 'price':
                    info_dict['lowest price'] = info_dict[value]
        except:
            for key, value in self.LISTING_BASIC_INFO_FIELDS.items():
                info_dict[value] = None
                if key == 'price':
                    info_dict['lowest price'] = None

        # Extract other specs
        specs_div = self.driver.find_element(By.CSS_SELECTOR, self.LISTING_SPECS_SELECTOR)
        specs_div_content = specs_div.get_attribute('outerHTML')
        specs_list = BeautifulSoup(specs_div_content, 'html.parser')

        specs_dict = {}
        for index, li in enumerate(specs_list.find_all('li', {'class': 'list-item'})):
            key = li.find('span', {'id': f'spec-key-{index}'}).text.strip()
            specs_dict[key] = li.find('span', {'id': f'spec-value-{index}'}).text.strip()

        for field in self.LISTING_SPECS_FIELDS:
            info_dict[field.lower()] = specs_dict.get(field, None)
        self.output_listing_csv(info_dict)
        return info_dict

        

def main():
    bot = AutotraderMainBot()
    # bot.run(pages = 1)
    bot.extract_listing_info()


if __name__ == "__main__":
    main()
