from abc import abstractmethod
from datetime import datetime, date, timedelta

from pymongo import MongoClient

from casemine.constants import CRAWL_DATABASE_IP, DATABASE_PORT, DATABASE_NAME, \
    TEST_COLLECTION, CONFIG_COLLECTION


class CaseMineCrawl:
    def __init__(self):
        self.end_date = None
        self.start_date = None
        self.crawled_till = None

    def execute_job(self, class_name):
        dbObj = self.get_crawl_config_details(class_name)
        str(dbObj.get('CrawledTill'))
        self.crawled_till = dbObj.get('CrawledTill')
        records = self.crawling(self.crawled_till)
        self.set_crawl_config_details(class_name, self.crawled_till)

    def crawling(self, crawled_till) -> int:
        # Initialize the list with retro months
        retro_months = [-1, -3, -6, -12]

        # Get the current date and day of the week
        self.end_date = datetime.now()
        day = self.end_date.weekday()  # Monday is 0 and Sunday is 6

        # Add extra retro months based on the day of the week
        if day == 5:  # Saturday
            retro_months.append(-24)
        elif day == 6:  # Sunday
            retro_months.append(-36)
        # Initialize date ranges dictionary
        date_ranges = {}
        # Populate date ranges based on the day of the week
        if day == 6:  # Sunday
            self.start_date = self.end_date - timedelta(days=7)
            date_ranges[self.start_date] = self.end_date
        elif day == 0:  # Monday
            self.start_date = self.end_date - timedelta(days=14)
            monday_end_date = self.end_date - timedelta(days=7)
            date_ranges[self.start_date] = monday_end_date
        else:
            crawlled_till = datetime.strptime(crawled_till, "%d/%m/%Y")
            date_ranges[crawlled_till] = self.end_date

        # Add retro month ranges to the date ranges
        for retro_month in retro_months:
            retro_end_date = self.end_date + timedelta(
                days=retro_month * 30)  # Approximate month length
            retro_start_date = retro_end_date - timedelta(days=1)
            date_ranges[retro_start_date] = retro_end_date

        # Crawl all date ranges
        count = 0
        for self.start_date, self.end_date in date_ranges.items():
            count = count + self.crawling_range(self.start_date, self.end_date)

        return count

    @abstractmethod
    def crawling_range(self, start_date: datetime, end_date: datetime) -> int:
        pass

    @staticmethod
    def get_crawl_config_details(class_name):
        client = MongoClient('mongodb://'+CRAWL_DATABASE_IP+':'+str(DATABASE_PORT)+'/')
        db = client[DATABASE_NAME]
        crawl_config_collection = db[CONFIG_COLLECTION]
        query = {'ClassName': class_name}
        cursor = crawl_config_collection.find(query)
        document = None
        for doc in cursor:
            document = doc
            break
        return document

    @staticmethod
    def set_crawl_config_details(class_name, crawled_till):
        client = MongoClient("mongodb://"+CRAWL_DATABASE_IP+":"+str(DATABASE_PORT))
        db = client[DATABASE_NAME]
        crawl_config = db[CONFIG_COLLECTION]

        # Query the collection
        query = {"ClassName": class_name}
        crawl_cursor = crawl_config.find(query)
        # Get the object to update
        object = None
        for document in crawl_cursor:
            object = document

        if object:
            # Update the document with the new "CrawledTill" value
            crawl_config.update_one({'_id': object['_id']},
                {'$set': {'CrawledTill': crawled_till}}
                # Replace with the actual value
            )
            # Update the document with the current date for "CrawlingDate"
            crawl_config.update_one({'_id': object['_id']},
                {'$set': {'CrawlingDate': datetime.now()}})
        # Close the MongoDB connection
        client.close()




