import os
from abc import abstractmethod
from datetime import datetime, timedelta

import requests
from pymongo import MongoClient

from casemine import constants
from casemine.casemine_util import CasemineUtil
from casemine.constants import CRAWL_DATABASE_IP, DATABASE_PORT, \
    MAIN_DATABASE_IP, DATABASE_NAME, CONFIG_COLLECTION, MAIN_PDF_PATH, \
    TEMP_PDF_PATH

class CaseMineCrawl:
    mongo1 = MongoClient(
        'mongodb://' + CRAWL_DATABASE_IP + ':' + str(DATABASE_PORT) + '/')
    mongo2 = MongoClient(
        'mongodb://' + MAIN_DATABASE_IP + ':' + str(DATABASE_PORT) + '/')

    # Access databases
    db1 = mongo1[constants.DATABASE_NAME]

    # Access collections
    judgements_collection = db1[constants.MAIN_COLLECTION]
    # judgements_collection = db1[constants.TEST_COLLECTION]

    config_collection = db1[constants.CONFIG_COLLECTION]

    # flag for duplicate
    flag = False

    def __init__(self):
        self.end_date = None
        self.start_date = None
        self.crawled_till = None

    def execute_job(self, class_name):
        dbObj = self.get_crawl_config_details(class_name)
        str(dbObj.get('CrawledTill'))
        self.crawled_till = dbObj.get('CrawledTill')
        records = self.crawling(self.crawled_till)

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
        # for retro_month in retro_months:
        #     retro_end_date = self.end_date + timedelta(
        #         days=retro_month * 30)  # Approximate month length
        #     retro_start_date = retro_end_date - timedelta(days=1)
        #     date_ranges[retro_start_date] = retro_end_date

        # Crawl all date ranges
        count = 0
        for self.start_date, self.end_date in date_ranges.items():
            count = count + self.crawling_range(self.start_date, self.end_date)
            # count=count+self.crawling_range(datetime(2025,1,1),datetime.today())
        return count

    def update_ark_data(self, data):
        pdf_url = data.get('pdf_url')
        case_title = data.get('title')
        case_date = data.get('date')
        class_name = data.get('class_name')
        query_for_duplication = {"date": case_date, "pdf_url": pdf_url, "title": case_title, 'class_name': class_name}
        duplicate = self.judgements_collection.find_one(query_for_duplication)
        object_id = None
        if duplicate is None:
            return self._process_opinion(data)
        else:
            object_id = duplicate.get("_id")
            processed = duplicate.get("processed")
            filter_query = {'_id': object_id}
            if int(processed) == 10:
                processed = 5
            update_query = {'$set': {"docket": data.get("docket"), "crawledAt": datetime.today(), "processed": processed, "html_url": data.get("html_url"), "response_html": data.get("response_html")}}
            self.judgements_collection.update_one(filter_query, update_query)
            print(f"Duplicate {object_id} updated.")
            return True

    @staticmethod
    def get_crawl_config_details(class_name):
        client = MongoClient(
            'mongodb://' + CRAWL_DATABASE_IP + ':' + str(DATABASE_PORT) + '/')
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
        client = MongoClient(
            "mongodb://" + CRAWL_DATABASE_IP + ":" + str(DATABASE_PORT))
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

    def _process_opinion(self, data) -> bool:
        self.flag = False
        objId = None
        try:
            objId = self._fetch_duplicate(data)
        except Exception as ex:
            if not str(ex).__eq__("Judgment already Exists!"):
                raise Exception(ex)

        if objId is not None:
            contentPdf = self.download_pdf(data, objId)
        # flag = saveContent(judId, contentPdf)
        return self.flag

    def _fetch_duplicate(self, data):
        pdf_url = str(data.get("pdf_url"))
        title = data.get("title")
        date = data.get("date")
        docket = data.get("docket")
        html_url = data.get("html_url")
        court_name = data.get("court_name")
        object_id = None
        if pdf_url.__eq__("") or (pdf_url is None) or pdf_url.__eq__("null"):
            if html_url.__eq__("") or (html_url is None) or html_url.__eq__("null"):
                return object_id
            else:
                query1 = {"html_url":html_url}
                dup1 = self.judgements_collection.find_one(query1)
                if dup1 is None:
                    inserted_doc=self.judgements_collection.insert_one(data)
                    object_id = inserted_doc.inserted_id

                    self.flag=True
                else:
                    query2 = {"court_name":court_name,"date":date, "title":title,"docket":docket}
                    dup2 = self.judgements_collection.find_one(query2)
                    if dup2 is None:
                        inserted_doc = self.judgements_collection.insert_one(data)
                        object_id = inserted_doc.inserted_id
                        self.flag = True
                    else:
                        # Check if the document already exists and has been processed
                        processed = dup2.get("processed")
                        if processed == 10:
                            raise Exception("Judgment already Exists!")  # Replace with your custom DuplicateRecordException
                        else:
                            object_id = dup2.get("_id")
        else:
            query3 = {"pdf_url":pdf_url}
            dup = self.judgements_collection.find_one(query3)
            if dup is None:
                query4 = {"court_name":court_name,"date":date, "title":title,"docket":docket}
                dup2=self.judgements_collection.find_one(query4)
                if dup2 is None:
                    inserted_doc = self.judgements_collection.insert_one(data)
                    object_id = inserted_doc.inserted_id
                    self.flag = True
                else:
                    # Check if the document already exists and has been processed
                    processed = dup2.get("processed")
                    if processed == 10:
                        raise Exception("Judgment already Exists!")  # Replace with your custom DuplicateRecordException
                    else:
                        object_id = dup2.get("_id")
            else:
                # Check if the document already exists and has been processed
                processed = dup.get("processed")
                if processed == 10:
                    raise Exception("Judgment already Exists!")  # Replace with your custom DuplicateRecordException
                else:
                    object_id = dup.get("_id")
        return object_id

    def _fetch_duplicate_old(self, data):
        # Create query for duplication
        query_for_duplication = {"pdf_url": data.get("pdf_url"),"docket": data.get("docket"),"title": data.get("title")}
        # Find the document
        duplicate = self.judgements_collection.find_one(query_for_duplication)
        object_id = None
        if duplicate is None:
            # Insert the new document
            self.judgements_collection.insert_one(data)
            # Retrieve the document just inserted
            updated_data = self.judgements_collection.find_one(query_for_duplication)
            object_id = updated_data.get("_id")  # Get the ObjectId from the document
            self.flag = True
        else:
            # Check if the document already exists and has been processed
            processed = duplicate.get("processed")
            if processed == 10:
                raise Exception("Judgment already Exists!")  # Replace with your custom DuplicateRecordException
            else:
                object_id = duplicate.get(
                    "_id")  # Get the ObjectId from the existing document
        return object_id

    def download_pdf(self, data, objectId):
        pdf_url = data.__getitem__('pdf_url')
        html_url = data.__getitem__('html_url')
        year = int(data.__getitem__('year'))
        court_name = data.get('court_name')
        court_type = data.get('court_type')

        if str(court_type).__eq__('Federal'):
            state_name=data.get('circuit')
        else:
            state_name = data.get('state')
        opinion_type = data.get('opinion_type')

        if str(opinion_type).__eq__("Oral Argument"):
            path = MAIN_PDF_PATH + court_type + "/" + state_name + "/" + court_name + "/" + "oral arguments/" + str(year)
        else:
            path = MAIN_PDF_PATH + court_type + "/" + state_name + "/" + court_name + "/" + str(year)

        obj_id = str(objectId)
        download_pdf_path = os.path.join(path, f"{obj_id}.pdf")

        if pdf_url.__eq__("") or (pdf_url is None) or pdf_url.__eq__("null"):
            if html_url.__eq__("") or (html_url is None) or html_url.__eq__("null"):
                self.judgements_collection.update_one({"_id": objectId}, {
                    "$set": {"processed": 2}})
            else:
                self.judgements_collection.update_one({"_id": objectId}, {
                    "$set": {"processed": 0}})
        else:
            try:
                os.makedirs(path, exist_ok=True)
                proxy = CasemineUtil.get_us_proxy()
                response = requests.get(url=pdf_url, headers={
                    "User-Agent": "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:130.0) Gecko/20100101 Firefox/130.0"},
                    proxies={"http": f"{proxy.ip}:{proxy.port}",
                             "https": f"{proxy.ip}:{proxy.port}"}, timeout=120)
                response.raise_for_status()
                with open(download_pdf_path, 'wb') as file:
                    file.write(response.content)
                self.judgements_collection.update_one({"_id": objectId},
                                                      {"$set": {"processed": 0}})
            except requests.RequestException as e:
                print(f"Error while downloading the PDF: {e}")
                self.judgements_collection.update_many({"_id": objectId}, {
                    "$set": {"processed": 2}})
        return download_pdf_path

    @abstractmethod
    def crawling_range(self, start_date: datetime, end_date: datetime) -> int:
        pass

    @abstractmethod
    def get_court_name(self):
        pass

    @abstractmethod
    def get_court_type(self):
        pass

    @abstractmethod
    def get_class_name(self):
        pass

    @abstractmethod
    def get_state_name(self):
        pass