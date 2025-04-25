import os
from datetime import datetime
import requests
from bson import ObjectId
from pymongo import MongoClient
from collections import namedtuple

# Initialize proxy index
Proxy = namedtuple("Proxy", ["ip", "port"])

# List of US proxies
US_PROXIES = [
	Proxy("136.0.186.20",6381),
	Proxy("136.0.194.45",6782),
	Proxy("92.113.3.93",6102),
	Proxy("38.170.189.230",9796),
	Proxy("216.74.118.170",6325),
	Proxy("45.249.59.45",6021),
	Proxy("136.0.105.114",6124),
	Proxy("43.245.117.235",5819),
	Proxy("192.241.118.37",8604),
	Proxy("23.27.208.154",5864)
]
us_proxy_index = -1

class CasemineUtil:

    @staticmethod
    def get_us_proxy():
        global us_proxy_index
        if us_proxy_index >= len(US_PROXIES) - 1:
            us_proxy_index = 0
        else:
            us_proxy_index += 1
        return US_PROXIES[us_proxy_index]

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
