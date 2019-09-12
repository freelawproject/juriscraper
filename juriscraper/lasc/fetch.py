from ..lib.log_tools import make_default_logger
import json, re
import datetime
from dateutil.rrule import rrule, WEEKLY

logger = make_default_logger()


class LASCSearch(object):
    """

    """

    def __init__(self, session):
        """

        :param lasc:
        """
        self.session = session
        self.api_base = "https://media.lacourt.org/api/AzureApi/"

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

    def check_success(self, r):

        if json.loads(r.text)['IsSuccess'] == True:
            logger.info(u'Successful query into LASC map')
            self.case_data = r.text
        else:
            logger.info(u'Failure to query into LASC map')

    def _get_json_from_internal_case_id(self, internal_case_id):
        """
         # This returns the JSON value of the store
        :param internal_case_id:
        :return:
        """

        r = self.session.get(self.GetCaseDetail % (self.api_base, internal_case_id))
        self.check_success(r)


    def query_cases_by_date(self, start, end):
        """Query LASC for a list of cases between two dates (inclusive)

        The LASC interface only allows queries of up to seven days at a time.
        If a wider request is made, break it into multiple smaller requests and
        append them together.

        :param start: A date object to start the query
        :param end: A date object to end the query
        :return: A list of case metadata objects
        """
        end = min(end, datetime.datetime.today())
        weekly_dates = rrule(freq=WEEKLY, dtstart=start, until=end)
        cases = []
        for dt in weekly_dates:
            start_str = dt.strftime('%m-%d-%Y')
            # Ensure end_str does not exceed the user's request. This may
            # happen on the last iteration.
            seven_days_later = dt + datetime.timedelta(days=7)
            end_str = min(seven_days_later, end).strftime('%m-%d-%Y')
            date_query_url = "%sGetRecentCivilCases/%s/%s" % (
                self.api_base, start_str, end_str)
            r = self.session.get(date_query_url)
            cases.extend(r.json()['ResultList'])

        return cases


    def _get_pdf_from_url(self, pdf_url):
        """
        # Using the unique internal case id information and document id we can collect all the pdfs

        :param pdf_url:
        :return:
        """

        logger.info(u'Api ViewDocument called.  Downloading PDF ')
        self.pdf_data = self.session.get(pdf_url).content


    def _parse_date_data(self):
        logger.info(u'Parsing Date Data')
        datum = json.loads(self.date_case_list)['ResultList']

        for data in datum:
            for k, v in data.items():
                data["_".join(l.lower() for l in re.findall('[A-Z][^A-Z]*', k))
                    .replace("_i_d", "_id").replace("disp_","disposition_")] = data.pop(k)

            data['case_id'] = data['internal_case_id']
            if data['judge_code'] == None:
                data['judge_code'] = ""
            if data['case_type_code'] == None:
                data['case_type_code'] = ""
            del data['internal_case_id']

        self.normalized_date_data = datum

    def _parse_case_data(self):
        """

        :return:
        """
        logger.info(u'Parsing Data')

        data = json.loads(self.case_data)['ResultList'][0]['NonCriminalCaseInformation']

        # Docket Normalization
        clean_data = {}
        clean_data['QueuedCase'] = []
        clean_data['LASCPDF'] = []
        clean_data['LASCJSON'] = []

        docket = {}
        docket['date_filed'] = datetime.datetime.strptime(data['CaseInformation']['FilingDate'][0:10],
                                                                '%Y-%m-%d').date()
        docket['date_disposition'] = None
        docket['docket_number'] = data['CaseInformation']['CaseNumber'].strip()
        docket['district'] = data['CaseInformation']['District'].strip()
        docket['division_code'] = data['CaseInformation']['DivisionCode'].strip()
        docket['disposition_type'] = data['CaseInformation']['DispositionType']
        docket['disposition_type_code'] = ""
        docket['case_type_str'] = data['CaseInformation']['CaseTypeDescription']
        docket['case_type_code'] = data['CaseInformation']['CaseType']
        docket['case_name'] = data['CaseInformation']['CaseTitle'].strip()
        docket['judge_code'] = ""
        docket['judge_name'] = data['CaseInformation']['JudicialOfficer']
        docket['courthouse_name'] = data['CaseInformation']['Courthouse']

        if data['CaseInformation']['StatusDate'] != None:
            docket['date_status'] = data['CaseInformation']['StatusDate']
            """Need to add in timezone support here"""
            docket['date_status'] = datetime.datetime. \
                strptime(data['CaseInformation']['StatusDate'], '%m/%d/%Y') \
                .strftime('%Y-%m-%d %H:%M:%S%z')
        else:
            docket['date_status'] = data['CaseInformation']['StatusDate']

        docket['status_code'] = data['CaseInformation']['StatusCode'] if data['CaseInformation'][
                                                                                   'StatusCode'] != None else ""
        docket['status_str'] = data['CaseInformation']['Status']
        clean_data['Docket'] = docket


        # Register of Actions Normalization
        clean_data['Action'] = []
        for action in data['RegisterOfActions']:
            registered_action = {}
            registered_action['date_of_action'] = action['RegisterOfActionDate']
            registered_action['description'] = action['Description']
            registered_action['additional_information'] = action['AdditionalInformation']
            clean_data['Action'].append(registered_action)


        # Cross References Normalization
        clean_data['CrossReference'] = []
        for cross_ref in data['CrossReferences']:
            cross_reference = {}
            cross_reference['date_cross_reference'] = cross_ref['CrossReferenceDate']
            cross_reference['cross_reference_docket_number'] = cross_ref['CrossReferenceCaseNumber']
            cross_reference['cross_reference_type'] = cross_ref['CrossReferenceTypeDescription']
            clean_data['CrossReference'].append(cross_reference)


        # Documents Filed
        clean_data['DocumentFiled'] = []
        for doc_filed in data['DocumentsFiled']:
            document = {}
            document['date_filed'] = doc_filed['DateFiled']
            document['memo'] = doc_filed['Memo'] if doc_filed['Memo'] != None else ""
            document['document_type'] = doc_filed['Document'] if doc_filed['Document'] != None else ""
            document['party_str'] = doc_filed['Party'] if doc_filed['Party'] != None else ""
            clean_data['DocumentFiled'].append(document)


        clean_data['QueuedPDF'] = []
        clean_data['DocumentImage'] = []
        for doc_image in data['DocumentImages']:
            image = {}
            pdf_queue = {}
            image['date_processed'] = doc_image['createDate']
            image['date_filed'] = doc_image['docFilingDate']
            image['doc_id'] = doc_image['docId']
            image['page_count'] = doc_image['pageCount']
            image['document_type'] = doc_image['documentType'] if doc_image['documentType'] != None else ""
            image['document_type_code'] = doc_image['documentTypeID']
            image['image_type_id'] = doc_image['imageTypeId']
            image['app_id'] = doc_image['appId'] if doc_image['appId'] != None else ""
            image['odyssey_id'] = doc_image['OdysseyID'] if doc_image['OdysseyID'] != None else ""
            image['is_downloadable'] = doc_image['IsDownloadable']
            image['security_level'] = doc_image['securityLevel']
            image['description'] = doc_image['description']
            image['doc_part'] = doc_image['docPart'] if doc_image['docPart'] != None else ""
            image['is_available'] = False

            pdf_queue['internal_case_id'] = data['CaseInformation']['CaseID']
            pdf_queue['document_id'] = doc_image['docId']

            clean_data['QueuedPDF'].append(pdf_queue)
            clean_data['DocumentImage'].append(image)


        clean_data['Party'] = []
        for party in data['Parties']:
            party_obj = {}
            party_obj['attorney_name'] = party['AttorneyName']
            party_obj['attorney_firm'] = party['AttorneyFirm']
            party_obj['entity_number'] = party['EntityNumber']
            party_obj['party_name'] = party['Name']
            party_obj['party_flag'] = party['PartyFlag']
            party_obj['party_type_code'] = party['PartyTypeCode']
            party_obj['party_description'] = party['PartyDescription']
            clean_data['Party'].append(party_obj)


        clean_data['Proceeding'] = []
        for proceeding in data['PastProceedings']:
            event = {}
            event['past_or_future'] = 1
            event['date_proceeding'] = proceeding['ProceedingDate']
            event['proceeding_time'] = proceeding['ProceedingTime']
            event['proceeding_room'] = proceeding['ProceedingRoom']
            event['am_pm'] = proceeding['AMPM']
            event['memo'] = proceeding['Memo']
            event['courthouse_name'] = proceeding['CourthouseName']
            event['address'] = proceeding['Address']
            event['result'] = proceeding['Result']
            event['judge_name'] = proceeding['Judge']
            event['event'] = proceeding['Event']
            clean_data['Proceeding'].append(event)

        for proceeding in data['FutureProceedings']:
            event = {}
            event['past_or_future'] = 2
            event['date_proceeding'] = proceeding['ProceedingDate']
            event['proceeding_time'] = proceeding['ProceedingTime']
            event['proceeding_room'] = proceeding['ProceedingRoom']
            event['am_pm'] = proceeding['AMPM']
            event['memo'] = proceeding['Memo']
            event['courthouse_name'] = proceeding['CourthouseName']
            event['address'] = proceeding['Address']
            event['result'] = proceeding['Result']
            event['judge_name'] = proceeding['Judge']
            event['event'] = proceeding['Event']
            clean_data['Proceeding'].append(event)


        clean_data['TentativeRuling'] = []
        for ruling in data['TentativeRulings']:
            tenative_ruling = {}
            tenative_ruling['date_created'] = ruling['CreationDate']
            tenative_ruling['date_hearing'] = ruling['HearingDate']
            tenative_ruling['department'] = ruling['Department']
            tenative_ruling['ruling'] = ruling['Ruling']

            clean_data['TentativeRuling'].append(tenative_ruling)

        self.normalized_case_data = clean_data