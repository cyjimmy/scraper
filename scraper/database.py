import os
from supabase import create_client
from dotenv import load_dotenv

load_dotenv()

class Database:
  SUPABASE_URL = os.getenv("SUPABASE_URL")
  SUPABASE_KEY = os.getenv("SUPABASE_KEY")
  SNAPSHOT_TABLE_NAME = "scraped_listing"
  LISTING_TABLE_NAME = "listing_details"

  def __init__(self):
    self.supabase = create_client(self.SUPABASE_URL, self.SUPABASE_KEY)

  def insert_scraped_listing(self, data):
    self.supabase.table(self.SNAPSHOT_TABLE_NAME).insert(data).execute()

  def insert_listing_details(self, data):
    self.supabase.table(self.LISTING_TABLE_NAME).insert(data).execute()

  def check_url_exist(self, url):
    result = self.supabase.table(self.LISTING_TABLE_NAME).select("*").eq("url", url).execute()
    return len(result.data) > 0
  
  def update_listing_price(self, url, price):
    self.supabase.table(self.LISTING_TABLE_NAME).update({"lowest_price": price}).eq("url", url).execute()
  
def main():
  db = Database()
  # db.update_listing_price("https://www.autotrader.ca/a/acura/ilx/surrey/british%20columbia/19_12745170", 1000)
  print(db.check_url_exist("https://www.autotrader.ca/a/acura/ilx/surrey/british%20columbia/19_12745170"))

if __name__ == "__main__":
  main()
