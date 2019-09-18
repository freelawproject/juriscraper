from ..lib.log_tools import make_default_logger
from datetime import datetime, timedelta
from dateutil.rrule import rrule, WEEKLY

logger = make_default_logger()


class LASCSearch(object):
    """
    An object designed to search the LA Superior Court Media Access portal.
    It search by date, lookup individual cases and collect PDFs on those cases
    if made available by LA Media.

    """

    def __init__(self, session):

        self.session = session
        self.api_base = "media.lacourt.org/api/AzureApi/"

    def get_json_from_internal_case_id(self, internal_case_id):
        """
        Query LASC for the case json based on the internal case id

        :param internal_case_id:
        :return:
        """

        r = self.session.get("https://%sGetCaseDetail/%s" %
                             (self.api_base, internal_case_id))
        self._check_success(r)

        return self._parse_case_data(r.json())

    def query_cases_by_date(self, start, end):
        """Query LASC for a list of cases between two dates (inclusive)

        The LASC interface only allows queries of up to seven days at a time.
        If a wider request is made, break it into multiple smaller requests
        and append them together.

        :param start: A date object to start the query
        :param end: A date object to end the query
        :return: A list of case metadata objects
        """
        end = min(end, datetime.today())
        weekly_dates = rrule(freq=WEEKLY, dtstart=start, until=end)
        cases = []
        for dt in weekly_dates:
            start_str = dt.strftime('%m-%d-%Y')
            # Ensure end_str does not exceed the user's request. This may
            # happen on the last iteration.
            seven_days_later = dt + timedelta(days=7)
            end_str = min(seven_days_later, end).strftime('%m-%d-%Y')
            date_query_url = "https://%sGetRecentCivilCases/%s/%s" % (
                self.api_base, start_str, end_str)
            r = self.session.get(date_query_url)
            cases.extend(r.json()['ResultList'])

        # Normalizes the date data
        normal_cases = []
        for case in cases:
            clean_case = {
                "internal_case_id": case['InternalCaseID'],
                "judge_code": case['JudicialOfficer'],
                "case_type_code": case['CaseTypeCode']
            }
            normal_cases.append(clean_case)

        return normal_cases

    def get_pdf_from_url(self, pdf_url):
        """
        Using the unique internal case id information and
        document id we can collect all the pdfs

        :param pdf_url:
        :return:
        """

        logger.info(u'Api ViewDocument called.  Downloading PDF ')
        return self.session.get(pdf_url).content

    @staticmethod
    def _parse_case_data(case_data):
        """
        This function normalizes the json response we get from LA MAP

        :param case_data: A python object containing the docket data
        :return: The parsed data with normalized fields
        """
        logger.info(u'Parsing lasc data from returned JSON into normalized '
                    u'format')

        try:
            data = case_data['ResultList'][0]['NonCriminalCaseInformation']
        except TypeError:
            data = case_data[0]['NonCriminalCaseInformation']

        # Docket Normalization
        clean_data = {
            'QueuedCase': [],
            'LASCPDF': [],
            'LASCJSON': []
        }

        case_info = data['CaseInformation']

        docket = {
            'date_filed': datetime.strptime(
                case_info['FilingDate'][0:10], '%Y-%m-%d').date(),
            'date_disposition': None,
            'docket_number': case_info['CaseNumber'].strip(),
            'district': case_info['District'].strip(),
            'division_code': case_info['DivisionCode'].strip(),
            'disposition_type': case_info['DispositionType'],
            'disposition_type_code': "",
            'case_type_str': case_info['CaseTypeDescription'],
            'case_type_code': case_info['CaseType'],
            'case_name': case_info['CaseTitle'].strip(),
            'judge_code': "",
            'judge_name': case_info['JudicialOfficer'],
            'courthouse_name': case_info['Courthouse'],
        }

        if case_info['StatusDate'] is not None:
            docket['date_status'] = case_info['StatusDate']
            """Need to add in timezone support here"""
            docket['date_status'] = datetime. \
                strptime(case_info['StatusDate'], '%m/%d/%Y') \
                .strftime('%Y-%m-%d %H:%M:%S%z')
        else:
            docket['date_status'] = case_info['StatusDate']

        docket['status_code'] = case_info['StatusCode'] if \
            case_info['StatusCode'] is not None else ""

        docket['status_str'] = case_info['Status']
        clean_data['Docket'] = docket

        # Register of Actions Normalization
        clean_data['Action'] = []
        for action in data['RegisterOfActions']:
            registered_action = {
                'date_of_action': action['RegisterOfActionDate'],
                'description': action['Description'],
                'additional_information': action['AdditionalInformation']
            }
            clean_data['Action'].append(registered_action)

        # Cross References Normalization
        clean_data['CrossReference'] = []
        for cross_ref in data['CrossReferences']:
            cross_reference = {
                'date_cross_reference': cross_ref['CrossReferenceDate'],
                'cross_reference_docket_number': cross_ref[
                    'CrossReferenceCaseNumber'],
                'cross_reference_type': cross_ref[
                    'CrossReferenceTypeDescription']
            }
            clean_data['CrossReference'].append(cross_reference)

        # Documents Filed
        clean_data['DocumentFiled'] = []
        for doc_filed in data['DocumentsFiled']:
            document = {
                'date_filed': doc_filed['DateFiled'],
                'memo': doc_filed['Memo'] or "",
                'document_type': doc_filed['Document'] or "",
                'party_str': doc_filed['Party'] or ""
            }
            clean_data['DocumentFiled'].append(document)

        clean_data['QueuedPDF'] = []
        clean_data['DocumentImage'] = []

        for doc_image in data['DocumentImages']:
            image = {
                'date_processed': doc_image['createDate'],
                'date_filed': doc_image['docFilingDate'],
                'doc_id': doc_image['docId'],
                'page_count': doc_image['pageCount'],
                'document_type': doc_image['documentType'] or '',
                'document_type_code': doc_image['documentTypeID'],
                'image_type_id': doc_image['imageTypeId'],
                'app_id': doc_image['appId'] or "",
                'odyssey_id': doc_image['OdysseyID'] or '',
                'is_downloadable': doc_image['IsDownloadable'],
                'security_level': doc_image['securityLevel'],
                'description': doc_image['description'],
                'doc_part': doc_image['docPart'] or '',
                'is_available': False,
            }

            pdf_queue = {
                'internal_case_id': data['CaseInformation']['CaseID'],
                'document_id': doc_image['docId'],
            }

            clean_data['DocumentImage'].append(image)
            clean_data['QueuedPDF'].append(pdf_queue)

        clean_data['Party'] = []
        for party in data['Parties']:
            party_obj = {
                'attorney_name': party['AttorneyName'],
                'attorney_firm': party['AttorneyFirm'],
                'entity_number': party['EntityNumber'],
                'party_name': party['Name'],
                'party_flag': party['PartyFlag'],
                'party_type_code': party['PartyTypeCode'],
                'party_description': party['PartyDescription']
            }

            clean_data['Party'].append(party_obj)

        clean_data['Proceeding'] = []
        for proceeding in data['PastProceedings']:
            event = {
                'past_or_future': 1,
                'date_proceeding': proceeding['ProceedingDate'],
                'proceeding_time': proceeding['ProceedingTime'],
                'proceeding_room': proceeding['ProceedingRoom'],
                'am_pm': proceeding['AMPM'], 'memo': proceeding['Memo'],
                'courthouse_name': proceeding['CourthouseName'],
                'address': proceeding['Address'],
                'result': proceeding['Result'],
                'judge_name': proceeding['Judge'],
                'event': proceeding['Event']
            }
            clean_data['Proceeding'].append(event)

        for proceeding in data['FutureProceedings']:
            event = {
                'past_or_future': 2,
                'date_proceeding': proceeding['ProceedingDate'],
                'proceeding_time': proceeding['ProceedingTime'],
                'proceeding_room': proceeding['ProceedingRoom'],
                'am_pm': proceeding['AMPM'], 'memo': proceeding['Memo'],
                'courthouse_name': proceeding['CourthouseName'],
                'address': proceeding['Address'],
                'result': proceeding['Result'],
                'judge_name': proceeding['Judge'],
                'event': proceeding['Event']
            }
            clean_data['Proceeding'].append(event)

        clean_data['TentativeRuling'] = []
        for ruling in data['TentativeRulings']:
            tenative_ruling = {
                'date_created': ruling['CreationDate'],
                'date_hearing': ruling['HearingDate'],
                'department': ruling['Department'],
                'ruling': ruling['Ruling']
            }

            clean_data['TentativeRuling'].append(tenative_ruling)

        return clean_data

    @staticmethod
    def _check_success(self, r):
        if r.json()['IsSuccess']:
            self.case_data = r.text
            logger.info(u'Successful query into LASC map')
        else:
            logger.info(u'Failure to query into LASC map')
