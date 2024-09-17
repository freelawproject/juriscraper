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



    # Assume these are defined elsewhere in your code
    file_base_path = "/path/to/base/directory/"
    client = MongoClient('mongodb://localhost:27017/')
    db = client['your_database_name']

    # def get_court_name():
    #     # Implementation of get_court_name function
    #     pass

    # def get_collection():
    #     return db['your_collection_name']
