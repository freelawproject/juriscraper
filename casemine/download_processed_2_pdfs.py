import os

import requests
from bson import ObjectId
from pymongo import MongoClient
from casemine.constants import CRAWL_DATABASE_IP, DATABASE_PORT, DATABASE_NAME, \
    MAIN_COLLECTION

STATE='Northern Mariana Islands'
client = MongoClient("mongodb://"+CRAWL_DATABASE_IP+":"+str(DATABASE_PORT))
db = client[DATABASE_NAME]
collection = db[MAIN_COLLECTION]

# Query the collection
# query = {'state': STATE ,'processed':2}
query = {'circuit':'1st Circuit','processed':2}
# lst=["67358b58f2b8aa8ee26a1422","67359311f2b8aa8ee26a14ee","6735933af2b8aa8ee26a14fc","6735939ff2b8aa8ee26a1507","67359414f2b8aa8ee26a152e","67359492f2b8aa8ee26a1544","6735975dc1b626349b6cefe7","67359a2fc1b626349b6cf06e","67359e88c1b626349b6cf0e0","67359e96c1b626349b6cf0e4","67359f1cc1b626349b6cf0f9","6735a047c1b626349b6cf118","6735a113c1b626349b6cf12c","6735a41bc1b626349b6cf187","6735a55bc1b626349b6cf1af","6735a61ec1b626349b6cf1d7","6735a78cc1b626349b6cf1f0","6735a9aec1b626349b6cf22f","6735a20e0246406efd7107b2","6735a3019a3c0719f5fddba3",]
# for i in lst:
    # query = {'state':'Delaware',"_id":ObjectId(i)}
count=collection.count_documents(query)
print(count)
crawl_cursor = collection.find(query)
# print(i)
i=1
for doc in crawl_cursor:
    pdf_url = doc.get('pdf_url')
    year = doc.get('year')
    court_name = doc.get('court_name')
    court_type = doc.get('court_type')
    if str(court_type).__eq__('Federal'):
        state_name = doc.get('circuit')
    else:
        state_name = doc.get('state')
    objectId = doc.get('_id')
    update_query = {}
    if not state_name is None:
        path = "/synology/PDFs/US/juriscraper/" + court_type + "/" + state_name + "/" + court_name + "/" + str(year)
    else:
        path = "/synology/PDFs/US/juriscraper/" + court_type + "/" + court_name + "/" + str(year)
    obj_id = str(objectId)
    download_pdf_path = os.path.join(path, f"{obj_id}.pdf")
    os.makedirs(path, exist_ok=True)
    try:
        response = requests.get(url=pdf_url, proxies={"http": "p.webshare.io:9999","https": "p.webshare.io:9999"})
        response.raise_for_status()
        with open(download_pdf_path, 'wb') as file:
            file.write(response.content)
        update_query.__setitem__("processed", 0)
        collection.update_one({'_id':objectId},{'$set':update_query})
        print(f"{i} - {obj_id} updated")
        i = i + 1
    except Exception as e:
        print(f"{i} - Error while downloading the PDF: {e} for {objectId}")
        update_query.__setitem__("processed", 2)
        collection.update_one({"_id": objectId}, {"$set": update_query})
        i=i+1
client.close()
