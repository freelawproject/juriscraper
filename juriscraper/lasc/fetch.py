import requests
requests.packages.urllib3.disable_warnings(requests.packages.urllib3.exceptions.InsecureRequestWarning)
from ..lib.log_tools import make_default_logger

logger = make_default_logger()

class LASCDocket(object):
    def __init__(self, lasc):
        self.lasc = lasc
        self.date_url_query = "https://media.lacourt.org/api/AzureApi/GetRecentCivilCases/%s/%s"
        self.documnet_url = "https://media.lacourt.org/api/AzureApi/ViewDocument/%s/%s"
        self.date_case_list = None
        self.pdf_data = None

    # This returns the JSON value of the store
    def get_json_from_internal_case_id(self, internal_case_id):
        self.case_url = self.lasc.fetch_url % (internal_case_id)
        self.case_data = self.lasc.s.get(self.case_url, verify=False, allow_redirects=True).text

    # date string is MM-DD-YYYY (ex. 12-31-2018)
    # This query will need to be repeated back dated to get files uploaded later and added to the database
    def get_case_list_for_date(self, date_string):
        self.date_query = self.date_url_query % (date_string, date_string)
        self.date_case_list = self.lasc.s.get(self.date_query, verify=False, allow_redirects=True).text

    # Using the unique internal case id information and document id we can collect all the pdfs
    def get_pdf_by_case_and_document_id(self, case_id, doc_id):
        self.pdf_url = self.documnet_url % (case_id, doc_id)
        self.pdf_data = self.lasc.s.get(self.pdf_url, verify=False, allow_redirects=False).content

