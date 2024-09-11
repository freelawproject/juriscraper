from datetime import date, datetime

import pymongo
from pymongo import MongoClient

from casemine.constants import CRAWL_DATABASE_IP, DATABASE_NAME, DATABASE_PORT

client = MongoClient(f"mongodb://{CRAWL_DATABASE_IP}:{str(DATABASE_PORT)}/")
db = client[DATABASE_NAME]
crawl_config_collection = db["JuriscrapperCrawlConfig"]
dict = {
    "ClassName": "ca1",
    "CrawlTill": "01/01/2024",
    "BaseUrl": "https://www.ca1.uscourts.gov/opn",
    "CrawlingDateAt": datetime.now(),
}
print(date.today())
# crawl_config_collection.insert_one(dict)
