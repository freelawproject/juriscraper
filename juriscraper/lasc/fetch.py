from ..lib.log_tools import make_default_logger
import json, re
import datetime

logger = make_default_logger()

class LASCSearch(object):
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
        self.normalized_case_data = None
        self.normalized_date_data = None

    def check_success(self, *args, **kwargs):


        if json.loads(args[0].text)['IsSuccess'] == True:
            logger.info(u'Successful query into LASC map')
            self.case_data = args[0].text
        else:
            logger.info(u'Failure to query into LASC map')

    def _get_json_from_internal_case_id(self, internal_case_id):
        """
         # This returns the JSON value of the store
        :param internal_case_id:
        :return:
        """

        self.lasc.get(self.GetCaseDetail % (self.api_base, internal_case_id), hooks={'response': [self.check_success]})


    def _get_case_list_for_last_seven_days(self):
        dt = datetime.datetime.today()
        date_string = dt.strftime('%m-%d-%Y')
        minus_seven = datetime.timedelta(days=-7)
        last_week = (dt + minus_seven).strftime('%m-%d-%Y')
        self.date_query = self.GetRecentCivilCases % (self.api_base, last_week, date_string)
        self.date_case_list = self.lasc.get(self.date_query).text


    def _get_case_list_for_date(self, date_string):
        """
        # date string is MM-DD-YYYY (ex. 12-31-2018)
        # This query will need to be repeated back dated to get files uploaded later and added to the database

        :param date_string:
        :return:
        """
        self.date_query = self.GetRecentCivilCases % (self.api_base, date_string, date_string)
        self.date_case_list = self.lasc.get(self.date_query).text


    def _get_pdf_by_case_and_document_id(self, case_id, doc_id):
        """
        # Using the unique internal case id information and document id we can collect all the pdfs

        :param case_id:
        :param doc_id:
        :return:
        """

        logger.info(u'Api ViewDocument called.  Downloading PDF ')
        self.pdf_url = self.ViewDocument % (self.api_base, case_id, doc_id)
        self.pdf_data = self.lasc.get(self.pdf_url).content


    def _get_internal_id(self, *args, **kwargs):
        self.internal_case_id = json.loads(args[0].text)['ResultList'][0]['NonCriminalCases'][0]['CaseID']


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
        self.lasc.get(self.case_search_url, hooks={'response': [self._get_internal_id]})
        self._get_json_from_internal_case_id(self.internal_case_id)



    # Future function to check for updates to case by ID
    def _check_for_update_to_case(self, internal_case_id):
        """

        :param internal_case_id:
        :return:
        """

        pass


    def _parse_date_data(self):
        logger.info(u'Parsing Date Data')
        datum = json.loads(self.date_case_list)['ResultList']

        for data in datum:
            for k, v in data.items():
                data["_".join(l.lower() for l in re.findall('[A-Z][^A-Z]*', k)).replace("_i_d", "_id").replace("disp_", "disposition_")] = data.pop(k)
            data['case_id'] = data['internal_case_id']

        self.normalized_date_data = datum



    def _parse_case_data(self):
        logger.info(u'Parsing Data')

        datum = json.loads(self.case_data)['ResultList'][0]['NonCriminalCaseInformation']
        for x in datum:
            data = datum[x]

            if datum[x] != None:
                if x == "CaseInformation":
                    for k, v in data.items():
                        kj = k[:1].upper() + k[1:]
                        data["_".join(l.lower() for l in re.findall('[A-Z][^A-Z]*', kj)).replace("_i_d", "_id").replace("disp_", "disposition_").replace("u_r_l", "url")] = data.pop(k)
                    data['internal_case_id'] = data['case_id']
                else:
                    for row in data:
                        for k, v in row.items():
                            kj = k[:1].upper() + k[1:]
                            row["_".join(l.lower() for l in re.findall('[A-Z][^A-Z]*', kj)).replace("_i_d", "_id")
                                            .replace("disp_", "disposition_")
                                            .replace("u_r_l", "url")
                                            .replace("c_r_s", "crs")
                                            .replace("a_m_p_m", "am_pm")
                                            .replace("c_x_c", "cxc")] = row.pop(k)

                if x == "DocumentImages":
                    for row in data:
                        row['document_url'] = self.ViewDocument % (self.api_base, datum['CaseInformation']['case_id'], row["doc_id"])


        self.normalized_case_data = datum



