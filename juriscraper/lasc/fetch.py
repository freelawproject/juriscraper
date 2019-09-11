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
        self.pdfs_data = []
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

    def _get_cases_around_dates(self, date1, date2):
        self.date_query = self.GetRecentCivilCases % (self.api_base, date1, date2)
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

    def _get_pdf_from_url(self, pdf_url):
        """
        # Using the unique internal case id information and document id we can collect all the pdfs

        :param case_id:
        :param doc_id:
        :return:
        """

        logger.info(u'Api ViewDocument called.  Downloading PDF ')

        self.pdf_data = self.lasc.get(pdf_url).content

    def _get_pdfs_from_urls(self, pdf_urls):
        """
        # Using the unique internal case id information and document id we can collect all the pdfs

        :param case_id:
        :param doc_id:
        :return:
        """

        # logger.info(u'Api ViewDocument called.  Downloading PDF ')
        # self.pdf_data = self.lasc.get(pdf_url).content

        from multiprocessing.dummy import Pool
        pool = Pool(10)

        futures = []
        for url in pdf_urls:
            futures.append(pool.apply_async(self.lasc.get, [url]))

        for future in futures:
            self.pdfs_data.append(future.get().content)

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
                data["_".join(l.lower() for l in re.findall('[A-Z][^A-Z]*', k)).replace("_i_d", "_id").replace("disp_",
                                                                                                               "disposition_")] = data.pop(
                    k)
            data['case_id'] = data['internal_case_id']
            if data['judge_code'] == None:
                data['judge_code'] = ""
            if data['case_type_code'] == None:
                data['case_type_code'] = ""
            del data['internal_case_id']

        self.normalized_date_data = datum

    def _parse_case_data(self):
        logger.info(u'Parsing Data')

        data = json.loads(self.case_data)['ResultList'][0]['NonCriminalCaseInformation']

        # Docket Normalization
        cd = {}
        cd['Docket'] = {}
        cd['Action'] = []
        cd['CrossReference'] = []
        cd['DocumentFiled'] = []
        cd['DocumentImage'] = []
        cd['Party'] = []
        cd['Proceeding'] = []
        cd['TentativeRuling'] = []
        cd['QueuedPDF'] = []
        cd['QueuedCase'] = []
        cd['LASCPDF'] = []
        cd['LASCJSON'] = []

        cd['Docket']['date_filed'] = datetime.datetime.strptime(data['CaseInformation']['FilingDate'][0:10],
                                                                '%Y-%m-%d').date()
        cd['Docket']['date_disposition'] = None
        cd['Docket']['docket_number'] = data['CaseInformation']['CaseNumber'].strip()
        cd['Docket']['district'] = data['CaseInformation']['District'].strip()
        cd['Docket']['division_code'] = data['CaseInformation']['DivisionCode'].strip()
        cd['Docket']['disposition_type'] = data['CaseInformation']['DispositionType']
        cd['Docket']['disposition_type_code'] = ""
        cd['Docket']['case_type_str'] = data['CaseInformation']['CaseTypeDescription']
        cd['Docket']['case_type_code'] = data['CaseInformation']['CaseType']
        cd['Docket']['case_name'] = data['CaseInformation']['CaseTitle'].strip()
        cd['Docket']['judge_code'] = ""
        cd['Docket']['judge_name'] = data['CaseInformation']['JudicialOfficer']
        cd['Docket']['courthouse_name'] = data['CaseInformation']['Courthouse']
        if data['CaseInformation']['StatusDate'] != None:
            cd['Docket']['date_status'] = data['CaseInformation']['StatusDate']
            """Need to add in timezone support here"""
            cd['Docket']['date_status'] = datetime.datetime. \
                strptime(data['CaseInformation']['StatusDate'], '%m/%d/%Y') \
                .strftime('%Y-%m-%d %H:%M:%S%z')
        else:
            cd['Docket']['date_status'] = data['CaseInformation']['StatusDate']
        cd['Docket']['status_code'] = data['CaseInformation']['StatusCode'] if data['CaseInformation'][
                                                                                   'StatusCode'] != None else ""
        cd['Docket']['status_str'] = data['CaseInformation']['Status']

        # Register of Actions Normalization
        for action in data['RegisterOfActions']:
            cdd = {}
            cdd['date_of_action'] = action['RegisterOfActionDate']
            cdd['description'] = action['Description']
            cdd['additional_information'] = action['AdditionalInformation']
            cd['Action'].append(cdd)

        # Cross References Normalization

        for cxref in data['CrossReferences']:
            cdd = {}
            cdd['date_cross_reference'] = cxref['CrossReferenceDate']
            cdd['cross_reference_docket_number'] = cxref['CrossReferenceCaseNumber']
            cdd['cross_reference_type'] = cxref['CrossReferenceTypeDescription']
            cd['CrossReference'].append(cdd)

        # Documents Filed
        for df in data['DocumentsFiled']:
            cdd = {}
            cdd['date_filed'] = df['DateFiled']
            cdd['memo'] = df['Memo'] if df['Memo'] != None else ""
            cdd['document_type'] = df['Document'] if df['Document'] != None else ""
            cdd['party_str'] = df['Party'] if df['Party'] != None else ""
            cd['DocumentFiled'].append(cdd)

        for df in data['DocumentImages']:
            cdd = {}
            cde = {}
            cdd['date_processed'] = df['createDate']
            cdd['date_filed'] = df['docFilingDate']

            cdd['doc_id'] = df['docId']
            cdd['page_count'] = df['pageCount']
            cdd['document_type'] = df['documentType'] if df['documentType'] != None else ""
            cdd['document_type_code'] = df['documentTypeID']

            cdd['image_type_id'] = df['imageTypeId']
            cdd['app_id'] = df['appId'] if df['appId'] != None else ""
            cdd['odyssey_id'] = df['OdysseyID'] if df['OdysseyID'] != None else ""
            cdd['is_downloadable'] = df['IsDownloadable']
            cdd['security_level'] = df['securityLevel']
            cdd['description'] = df['description']
            cdd['doc_part'] = df['docPart'] if df['docPart'] != None else ""
            cdd['is_available'] = False

            cde['internal_case_id'] = data['CaseInformation']['CaseID']
            cde['document_id'] = df['docId']
            cd['QueuedPDF'].append(cde)

            cd['DocumentImage'].append(cdd)

        for df in data['Parties']:
            cdd = {}
            cdd['attorney_name'] = df['AttorneyName']
            cdd['attorney_firm'] = df['AttorneyFirm']
            cdd['entity_number'] = df['EntityNumber']

            cdd['party_name'] = df['Name']
            cdd['party_flag'] = df['PartyFlag']
            cdd['party_type_code'] = df['PartyTypeCode']
            cdd['party_description'] = df['PartyDescription']

            cd['Party'].append(cdd)

        for df in data['PastProceedings']:
            cdd = {}
            cdd['past_or_future'] = 1
            cdd['date_proceeding'] = df['ProceedingDate']
            cdd['proceeding_time'] = df['ProceedingTime']
            cdd['proceeding_room'] = df['ProceedingRoom']
            cdd['am_pm'] = df['AMPM']
            cdd['memo'] = df['Memo']
            cdd['courthouse_name'] = df['CourthouseName']
            cdd['address'] = df['Address']
            cdd['result'] = df['Result']
            cdd['judge_name'] = df['Judge']
            cdd['event'] = df['Event']

            cd['Proceeding'].append(cdd)

        for df in data['FutureProceedings']:
            cdd = {}
            cdd['past_or_future'] = 2
            cdd['date_proceeding'] = df['ProceedingDate']
            cdd['proceeding_time'] = df['ProceedingTime']
            cdd['proceeding_room'] = df['ProceedingRoom']
            cdd['am_pm'] = df['AMPM']
            cdd['memo'] = df['Memo']
            cdd['courthouse_name'] = df['CourthouseName']
            cdd['address'] = df['Address']
            cdd['result'] = df['Result']
            cdd['judge_name'] = df['Judge']
            cdd['event'] = df['Event']
            cd['Proceeding'].append(cdd)

        for df in data['TentativeRulings']:
            cdd = {}
            cdd['date_created'] = df['CreationDate']
            cdd['date_hearing'] = df['HearingDate']
            cdd['department'] = df['Department']
            cdd['ruling'] = df['Ruling']

            cd['TentativeRuling'].append(cdd)

        self.normalized_case_data = cd