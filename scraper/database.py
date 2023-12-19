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

  def get_all_listing_urls(self):
    result = self.supabase.table(self.SNAPSHOT_TABLE_NAME).select("url").execute()
    urls = [item["url"] for item in result.data]
    return urls
  
def main():
  db = Database()
  new_listing = {"url": "123", "price": 123}
  db.insert_scraped_listing(new_listing)
  print(db.get_all_listing_urls())

if __name__ == "__main__":
  main()
