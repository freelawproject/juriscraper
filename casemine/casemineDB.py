from datetime import date, datetime

import pymongo

from casemine.constants import CRAWL_DATABASE_IP, DATABASE_NAME, \
    TEST_COLLECTION
from juriscraper.opinions.united_states.federal_appellate import scotus_slip, \
    cafc, ca1
from juriscraper.opinions.united_states.state import ala, alaska, ariz, ark, \
    cal, dc

dbClient = pymongo.MongoClient("mongodb://" + CRAWL_DATABASE_IP + ":27017/")

db = dbClient.get_database(DATABASE_NAME)
collection = db.get_collection(TEST_COLLECTION)
# case_data = {
#     'case_dates': datetime(2024, 7, 1),  # Convert to datetime object
#     'case_names': 'Trump v. United States',
#     'download_urls': 'https://www.supremecourt.gov/opinions/23pdf/23-939_e2pg.pdf',
#     'precedential_statuses': 'Published',
#     'blocked_statuses': False,
#     'date_filed_is_approximate': False,
#     'docket_numbers': '23-939',
#     'judges': 'John G. Roberts',
#     'citations': '603/1',
#     'case_name_shorts': 'Trump'
# }
#
# # Insert the dictionary into MongoDB
# result = collection.insert_one(case_data)
# print('value inserted')

site = dc.Site()
# Populate it with data, downloading the page if necessary
site.parse()

i = 1
for opinion in site:
    if(i<=10):
        opdate = opinion.get('case_dates')
        new_date = datetime(opdate.year, opdate.month, opdate.day)
        opinion.__setitem__('case_dates', new_date)
        collection.insert_one(opinion)
        print(f"{i} | {opinion.get('case_names')}")
        i=i+1

# for i in site:
#     print(i)

