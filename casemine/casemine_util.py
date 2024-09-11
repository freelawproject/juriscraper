import os
from datetime import datetime

import requests
from bson import ObjectId
from pymongo import MongoClient
class CasemineUtil:
    @staticmethod
    def compare_date(date: str, craw_date: str) -> int:
        formats = ["%d/%m/%Y", "%d-%m-%Y", "%d/%m/%y", "%d-%m-%y", "%d/%b/%Y"]
        date1 = None
        date2 = None
        # Try parsing the dates with different formats
        for fmt in formats:
            try:
                date1 = datetime.strptime(date, fmt)
                date2 = datetime.strptime(craw_date, fmt)
                return (date1 > date2) - (
                        date1 < date2)  # 1 if date1 > date2, -1 if date1 < date2, 0 if equal
            except ValueError:
                continue  # Try the next format
        # Log the error if no formats matched
        print(f"Error while parsing the dates: {date}, {craw_date}")
        return 0  # Return 0 if no valid format was found

    # def download_pdf(map,objectId):
    #     pdf_url = map['pdfUrl']
    #     year = int(data['judgment_Year'])
    #
    #     court_name = get_court_name()
    #
    #     dir_path = os.path.join(file_base_path, court_name, str(year))
    #
    #     obj_id = str(jud_id)
    #     download_pdf_path = os.path.join(dir_path, f"{obj_id}.pdf")
    #
    #     os.makedirs(dir_path, exist_ok=True)
    #
    #     try:
    #         response = requests.get(pdf_url)
    #         response.raise_for_status()
    #
    #         with open(download_pdf_path, 'wb') as file:
    #             file.write(response.content)
    #
    #         get_collection().update_one({"_id": jud_id},
    #             {"$set": {"processed": 0}})
    #     except requests.RequestException as e:
    #         print(f"Error while downloading the PDF: {e}")
    #         get_collection().update_many({"_id": jud_id},
    #             {"$set": {"processed": 2, "content": ""}})
    #
    #     return download_pdf_path

    # Assume these are defined elsewhere in your code
    file_base_path = "/path/to/base/directory/"
    client = MongoClient('mongodb://localhost:27017/')
    db = client['your_database_name']

    # def get_court_name():
    #     # Implementation of get_court_name function
    #     pass

    # def get_collection():
    #     return db['your_collection_name']
