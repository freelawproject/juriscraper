import json
from ..lib.log_tools import make_default_logger

logger = make_default_logger()

class LASC_Docket(object):
    """

    """
    def __init__(self, lasc):
        """

        :param lasc:
        """
        self.lasc = lasc
        self.api_base = "https://media.lacourt.org/api/AzureApi/"
        self.GetRecentCivilCases = "%sGetRecentCivilCases/%s/%s"
        self.ViewDocument = "%sViewDocument/%s/%s"
        self.GetCaseList = "%sGetCaseList/%s"
        self.GetCaseDetail = "%sGetCaseDetail/%s"

        self.date_case_list = None
        self.pdf_data = None
        self.success = None
        self.internal_case_id = None


    def _get_json_from_internal_case_id(self, internal_case_id):
        """
         # This returns the JSON value of the store
        :param internal_case_id:
        :return:
        """
        self.case_url = self.GetCaseDetail % (self.api_base, internal_case_id)
        self.case_data = self.lasc.get(self.case_url, verify=False, allow_redirects=True).text
        self.success = json.loads(self.case_data)['IsSuccess']

        if self.success == True:
            logger.info(u'Successful query into LASC map')

    def _get_case_list_for_date(self, date_string):
        """
        # date string is MM-DD-YYYY (ex. 12-31-2018)
        # This query will need to be repeated back dated to get files uploaded later and added to the database

        :param date_string:
        :return:
        """
        self.date_query = self.GetRecentCivilCases % (self.api_base, date_string, date_string)
        self.date_case_list = self.lasc.get(self.date_query, verify=False, allow_redirects=True).text


    def _get_pdf_by_case_and_document_id(self, case_id, doc_id):
        """
        # Using the unique internal case id information and document id we can collect all the pdfs

        :param case_id:
        :param doc_id:
        :return:
        """
        logger.info(u'Api ViewDocument called.  Downloading PDF ')
        self.pdf_url = self.ViewDocument % (self.api_base, case_id, doc_id)
        self.pdf_data = self.lasc.get(self.pdf_url, verify=False, allow_redirects=False).content

    # This function probably works 99% of the time.
    # But it is unknown how common if at all case numbers are repeated in unlimited cases.
    # Currently it grabs the first result, if a case number is not unique.
    def _get_case_by_case_id(self, case_id):
        """

        :param case_id:
        :return:
        """
        logger.info(u'Search case by case id only. Assumes first result is the only result.')

        self.case_search_url = self.GetCaseList % (self.api_base, case_id)
        self.internal_case_id = json.loads(self.lasc.get(self.case_search_url).text)['ResultList'][0]['NonCriminalCases'][0]['CaseID']
        self._get_json_from_internal_case_id(self.internal_case_id)


    # Future function to check for updates to case by ID
    def check_for_update_to_case(self, internal_case_id):
        """

        :param internal_case_id:
        :return:
        """
        pass