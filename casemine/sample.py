# import os
# import shutil
# import time
#
# import pdfkit
# from anyio import sleep
# from bs4 import BeautifulSoup
# from bson import ObjectId
# from exceptiongroup import catch
# from pymongo import MongoClient
# from selenium import webdriver
# from selenium.webdriver.chrome.service import Service
# from tldextract.tldextract import update
# from webdriver_manager.chrome import ChromeDriverManager
#
# from casemine.constants import CRAWL_DATABASE_IP, DATABASE_PORT, DATABASE_NAME, \
#     MAIN_COLLECTION
#
#
# # code starts from here
# client = MongoClient("mongodb://"+CRAWL_DATABASE_IP+":"+str(DATABASE_PORT))
# db = client[DATABASE_NAME]
# collection = db[MAIN_COLLECTION]
# # Query the collection
# query = {'state':'New York','processed':2}
# count=collection.count_documents(query)
# crawl_cursor = collection.find(query)
#
# print(count)
# # Get the object to update
# i=1
# for doc in crawl_cursor:
#     # print(f"{doc.get('_id')} {doc.get('pdf_url')} {doc.get('processed')}")
#     pdf_url = doc.get('pdf_url')
#     year = doc.get('year')
#     court_name = doc.get('court_name')
#     court_type = doc.get('court_type')
#     state_name = doc.get('state')
#     objectId = doc.get('_id')
#     update_query = {}
#     if str(pdf_url).__contains__('motions'):
#         update_query.__setitem__("opinion_type", "motion")
#     else:
#         update_query.__setitem__("opinion_type", "opinion")
#     try:
#         path = "/synology/PDFs/US/juriscraper/" + court_type + "/" + state_name + "/" + court_name + "/" + str(year)
#         obj_id = str(objectId)
#         download_pdf_path = os.path.join(path, f"{obj_id}.pdf")
#         os.makedirs(path, exist_ok=True)
#         if str(pdf_url).endswith(".htm"):
#             options = webdriver.ChromeOptions()
#             options.add_argument("--no-sandbox")
#             options.add_argument("--headless")
#             options.add_argument("--disable-dev-shm-usage")
#             options.add_argument(
#                 "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.107 Safari/537.36")
#             options.add_argument("--disable-blink-features=AutomationControlled")
#             proxy = "http://p.webshare.io:9999"  # Replace with your proxy
#             options.add_argument(f"--proxy-server={proxy}")
#             # Create a WebDriver instance
#             driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
#             driver.get(pdf_url)
#             driver_content = driver.page_source
#             if driver_content.__contains__('Sorry, but the page you requested') and driver_content.__contains__('We apologize for any inconvenience this may have caused you.'):
#                 raise Exception('Html not found')
#             soup = BeautifulSoup(driver_content, 'html.parser')
#             # print(soup.text)
#             center_divs = soup.find_all('div', align='center')
#             for div in center_divs:
#                 if div and div.find('input', {'value': 'Return to Decision List'}):
#                     div.decompose()
#             # Find all anchor tags and remove the href attribute
#             for tag in soup.find_all('a'):
#                 del tag['href']
#             # Print the modified HTML
#             modified_html = soup.prettify()
#             pdfkit.from_string(modified_html, download_pdf_path)
#             driver.quit()
#             update_query.__setitem__("response_html", modified_html)
#             update_query.__setitem__("processed", 0)
#
#             collection.update_one({'_id':objectId},{'$set':update_query})
#             print(f"{i} - {obj_id} updated")
#             i = i + 1
#
#         elif str(pdf_url).endswith(".pdf"):
#             download_dir = '/home/gaugedata/Downloads/us/juriscraper/new york/pdfs'  # Update with your desired directory
#             if not os.path.exists(download_dir):
#                 os.makedirs(download_dir)
#             options = webdriver.ChromeOptions()
#             options.add_argument("--no-sandbox")
#             options.add_argument("--headless")
#             options.add_argument("--window-size=1920x1080")
#             options.add_argument("--disable-dev-shm-usage")
#             options.add_argument("--disable-gpu")
#             options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.107 Safari/537.36")
#             options.add_argument("--disable-blink-features=AutomationControlled")
#
#             proxy = "http://p.webshare.io:9999"  # Replace with your proxy
#             options.add_argument(f"--proxy-server={proxy}")
#
#             # Set preferences for downloading PDFs automatically without a prompt
#             prefs = {"download.default_directory": download_dir,
#                      "download.prompt_for_download": False,
#                      "download.directory_upgrade": True,
#                      "plugins.always_open_pdf_externally": True}
#             options.add_experimental_option("prefs", prefs)
#             driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
#             # Navigate to the PDF URL
#             driver.get(pdf_url)
#             time.sleep(5)  # Adjust this time based on the file size and download speed
#             # Close the browser
#             driver.quit()
#             src_path = download_dir + "/" + pdf_url.split('/')[-1]
#             shutil.move(src_path, download_pdf_path)
#             update_query.__setitem__("processed", 0)
#             collection.update_one({'_id': objectId}, {'$set': update_query})
#             print(f"{i} - {obj_id} updated")
#             i=i+1
#         else:
#             print("wrong pdf_url extension")
#     except Exception as e:
#         print(f"{i} - Error while downloading the PDF: {e} for {objectId}")
#         update_query.__setitem__("processed", 2)
#         collection.update_one({"_id": objectId}, {"$set": update_query})
#         i=i+1
# client.close()

import os

import requests
from bson import ObjectId
from pymongo import MongoClient
from casemine.constants import CRAWL_DATABASE_IP, DATABASE_PORT, DATABASE_NAME, \
    MAIN_COLLECTION

client = MongoClient("mongodb://"+CRAWL_DATABASE_IP+":"+str(DATABASE_PORT))
db = client[DATABASE_NAME]
collection = db[MAIN_COLLECTION]
# Query the collection
query = {'state':'North Carolina','processed':2}
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
    state_name = doc.get('state')
    objectId = doc.get('_id')
    update_query = {}
    path = "/synology/PDFs/US/juriscraper/" + court_type + "/" + state_name + "/" + court_name + "/" + str(year)
    obj_id = str(objectId)
    download_pdf_path = os.path.join(path, f"{obj_id}.pdf")
    os.makedirs(path, exist_ok=True)
    try:
        response = requests.get(url=pdf_url, proxies={"http": "23.95.255.114:6698","https": "23.95.255.114:6698"})
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



# import os
# import shutil
# import time
#
# from selenium import webdriver
# from selenium.webdriver.chrome.service import Service
# from webdriver_manager.chrome import ChromeDriverManager
#
#
# # Specify the download directory
# download_dir = '/home/gaugedata/Downloads/us/pdfs/'  # Update with your desired directory
#
# # Create the directory if it doesn't exist
# if not os.path.exists(download_dir):
#     os.makedirs(download_dir)
#
# options = webdriver.ChromeOptions()
# options.add_argument("--no-sandbox")
# options.add_argument("--headless")
# options.add_argument("--window-size=1920x1080")  # Set window size (optional)
# options.add_argument("--disable-dev-shm-usage")
# options.add_argument("--disable-gpu")  # Optional: Disable GPU acceleration for headless mode
# options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.107 Safari/537.36")
# options.add_argument("--disable-blink-features=AutomationControlled")
#
# proxy = "http://p.webshare.io:9999"  # Replace with your proxy
# options.add_argument(f"--proxy-server={proxy}")
#
# # Set preferences for downloading PDFs automatically without a prompt
# prefs = {
#     "download.default_directory": download_dir,  # Directory where PDFs will be saved
#     "download.prompt_for_download": False,        # Disable the download prompt
#     "download.directory_upgrade": True,           # Ensure the download path is upgraded
#     "plugins.always_open_pdf_externally": True    # Open PDFs externally (instead of in the browser)
# }
#
# options.add_experimental_option("prefs", prefs)
#
# driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
#
# # URL of the page containing the PDF or direct PDF link
# pdf_url = 'https://www.nycourts.gov/reporter/motions/2024/2024_68508.pdf'  # Replace with the actual URL
#
# # Navigate to the PDF URL
# driver.get(pdf_url)
#
# # Wait for the download to complete (adjust time as needed)
# time.sleep(5)  # Adjust this time based on the file size and download speed
#
# # Close the browser
# driver.quit()
# print(f"PDF should be downloaded to: {download_dir}")
#
# dest_path='/home/gaugedata/Downloads/us/extras/'
#
# # Create the directory if it doesn't exist
# if not os.path.exists(dest_path):
#     os.makedirs(dest_path)
#
# # shutil.copy(src=download_dir+pdf_url.split('/')[-1],dst=dest_path+'objectId.pdf')
#
# # Move and rename the file
# shutil.move(src=download_dir+pdf_url.split('/')[-1],dst=dest_path+'faltu.pdf')
#
# print(f"File renamed and moved to: {dest_path}")

