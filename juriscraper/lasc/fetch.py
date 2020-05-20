from ..lib.log_tools import make_default_logger
from ..lib.utils import clean_court_object
from datetime import datetime, timedelta
from dateutil.rrule import rrule, WEEKLY

logger = make_default_logger()


class LASCSearch(object):
    """
    An object designed to search the LA Superior Court Media Access Portal
    (MAP). It searches by date, looks up individual cases, and collects PDFs on
    those cases if made available in the MAP.
    """

    def __init__(self, session):
        self.session = session
        self.api_base = "media.lacourt.org/api/AzureApi/"

    def get_json_from_internal_case_id(self, internal_case_id):
        """Query LASC for the case json based on the internal case id

        :param internal_case_id: An internal ID of the form, 19STCV25157;SS;CV
        :return: The parsed docket data for the case requested
        """
        r = self.session.get(
            "https://%sGetCaseDetail/%s" % (self.api_base, internal_case_id)
        )
        self._check_success(r)

        return self._parse_case_data(r.json())

    def query_cases_by_date(self, start, end):
        """Query LASC for a list of cases between two dates (inclusive)

        The LASC interface only allows queries of up to seven days at a time.
        If a wider request is made, break it into multiple smaller requests
        and append their results together.

        :param start: A date object to start the query
        :param end: A date object to end the query
        :return: A list of case metadata objects
        """
        start_str = start.strftime("%m-%d-%Y")
        end_str = end.strftime("%m-%d-%Y")
        date_query_url = "https://%sGetRecentCivilCases/%s/%s" % (
            self.api_base,
            start_str,
            end_str,
        )
        r = self.session.get(date_query_url)
        cases = r.json()["ResultList"]

        # Normalize the date data
        normal_cases = []
        for case in cases:
            clean_case = {
                "internal_case_id": case["InternalCaseID"],
                "judge_code": case["JudgeCode"] or "",
                "case_type_code": case["CaseTypeCode"] or "",
            }
            normal_cases.append(clean_case)

        return normal_cases

    def get_pdf_from_url(self, pdf_url):
        """Get a PDF from the MAP

        :param pdf_url: The URL to a particular PDF you wish to download
        :return: The binary PDF data
        """

        logger.info(u"Api ViewDocument called.  Downloading PDF ")
        return self.session.get(pdf_url).content

    @staticmethod
    def _parse_case_data(case_data):
        """
        This function normalizes the json docket data we get from LA MAP

        The MAP, mercifully, gives us JSON data, so this isn't too bad. The
        main task, then, is to convert the various field names it provides over
        to field names following our conventions.

        :param case_data: A python dict of a docket as gathered from the MAP
        (this will be JSON data in the MAP, but convert it to Python before
        calling this method.)
        :return: The parsed, cleaned, normalized data
        """
        logger.info(
            u"Parsing lasc data from returned JSON into normalized " u"format"
        )

        try:
            data = case_data["ResultList"][0]["NonCriminalCaseInformation"]
        except IndexError:
            # Some cases don't have any data at all, see: P4160;JCC;CV. When
            # this happens, Juriscraper returns nothing as well.
            return {}

        # Docket Normalization
        clean_data = {u"QueuedCase": [], u"LASCPDF": [], u"LASCJSON": []}

        case_info = data[u"CaseInformation"]

        docket = {
            u"date_filed": case_info[u"FilingDate"].date(),
            u"date_disposition": None,
            u"docket_number": case_info[u"CaseNumber"],
            u"district": case_info[u"District"],
            u"division_code": case_info[u"DivisionCode"],
            u"disposition_type": case_info[u"DispositionType"],
            u"disposition_type_code": u"",
            u"case_type_str": case_info[u"CaseTypeDescription"],
            u"case_type_code": case_info[u"CaseType"],
            u"case_name": case_info[u"CaseTitle"] or u"",
            u"judge_code": u"",
            u"judge_name": case_info[u"JudicialOfficer"],
            u"courthouse_name": case_info[u"Courthouse"],
        }

        if case_info[u"StatusDate"] is not None:
            docket["date_status"] = datetime.strptime(
                case_info["StatusDate"], "%m/%d/%Y"
            ).date()
        else:
            docket[u"date_status"] = case_info[u"StatusDate"]

        docket[u"status_code"] = case_info[u"StatusCode"] or ""
        docket[u"status_str"] = case_info[u"Status"]
        clean_data[u"Docket"] = docket

        # Register of Actions normalization
        clean_data[u"Action"] = []
        for action in data[u"RegisterOfActions"]:
            registered_action = {
                u"date_of_action": action[u"RegisterOfActionDate"],
                u"description": action[u"Description"],
                u"additional_information": action[u"AdditionalInformation"],
            }
            clean_data[u"Action"].append(registered_action)

        # Cross References normalization
        clean_data[u"CrossReference"] = []
        for cross_ref in data[u"CrossReferences"]:
            cross_reference = {
                u"date_cross_reference": cross_ref[u"CrossReferenceDate"],
                u"cross_reference_docket_number": cross_ref[
                    u"CrossReferenceCaseNumber"
                ]
                or u"",
                u"cross_reference_type": cross_ref[
                    u"CrossReferenceTypeDescription"
                ],
            }
            clean_data[u"CrossReference"].append(cross_reference)

        # Documents Filed
        clean_data[u"DocumentFiled"] = []
        for doc_filed in data[u"DocumentsFiled"]:
            document = {
                u"date_filed": doc_filed[u"DateFiled"],
                u"memo": doc_filed[u"Memo"] or "",
                u"document_type": doc_filed[u"Document"] or "",
                u"party_str": doc_filed[u"Party"] or "",
            }
            clean_data[u"DocumentFiled"].append(document)

        clean_data[u"QueuedPDF"] = []
        clean_data[u"DocumentImage"] = []
        for doc_image in data[u"DocumentImages"]:
            image = {
                u"date_processed": doc_image[u"createDate"],
                u"date_filed": doc_image[u"docFilingDate"],
                u"doc_id": doc_image[u"docId"],
                u"page_count": doc_image[u"pageCount"],
                u"document_type": doc_image[u"documentType"] or "",
                u"document_type_code": doc_image[u"documentTypeID"],
                u"image_type_id": doc_image[u"imageTypeId"],
                u"app_id": doc_image[u"appId"] or u"",
                u"odyssey_id": doc_image[u"OdysseyID"] or "",
                u"is_downloadable": doc_image[u"IsDownloadable"],
                u"security_level": doc_image[u"securityLevel"],
                u"description": doc_image[u"description"] or "",
                u"doc_part": doc_image[u"docPart"] or "",
                u"is_available": False,
            }

            pdf_queue = {
                u"internal_case_id": data[u"CaseInformation"][u"CaseID"],
                u"document_id": doc_image[u"docId"],
            }

            clean_data[u"DocumentImage"].append(image)
            clean_data[u"QueuedPDF"].append(pdf_queue)

        clean_data[u"Party"] = []
        for party in data[u"Parties"]:
            party_obj = {
                u"attorney_name": party[u"AttorneyName"],
                u"attorney_firm": party[u"AttorneyFirm"],
                u"entity_number": party[u"EntityNumber"],
                u"party_name": party[u"Name"],
                u"party_flag": party[u"PartyFlag"],
                u"party_type_code": party[u"PartyTypeCode"] or "",
                u"party_description": party[u"PartyDescription"] or "",
            }
            clean_data["Party"].append(party_obj)

        clean_data[u"Proceeding"] = []
        for proceeding in data[u"PastProceedings"]:
            event = {
                u"past_or_future": 1,
                u"date_proceeding": proceeding[u"ProceedingDate"],
                u"proceeding_time": proceeding[u"ProceedingTime"],
                u"proceeding_room": proceeding[u"ProceedingRoom"],
                u"am_pm": proceeding[u"AMPM"],
                u"memo": proceeding[u"Memo"],
                u"courthouse_name": proceeding[u"CourthouseName"],
                u"address": proceeding[u"Address"],
                u"result": proceeding[u"Result"],
                u"judge_name": proceeding[u"Judge"],
                u"event": proceeding[u"Event"],
            }
            clean_data[u"Proceeding"].append(event)

        for proceeding in data[u"FutureProceedings"]:
            event = {
                u"past_or_future": 2,
                u"date_proceeding": proceeding[u"ProceedingDate"],
                u"proceeding_time": proceeding[u"ProceedingTime"],
                u"proceeding_room": proceeding[u"ProceedingRoom"],
                u"am_pm": proceeding[u"AMPM"],
                u"memo": proceeding[u"Memo"],
                u"courthouse_name": proceeding[u"CourthouseName"],
                u"address": proceeding[u"Address"],
                u"result": proceeding[u"Result"],
                u"judge_name": proceeding[u"Judge"],
                u"event": proceeding[u"Event"],
            }
            clean_data[u"Proceeding"].append(event)

        clean_data[u"TentativeRuling"] = []
        for ruling in data[u"TentativeRulings"]:
            tentative_ruling = {
                u"date_created": ruling[u"CreationDate"],
                u"date_hearing": ruling[u"HearingDate"],
                u"department": ruling[u"Department"],
                u"ruling": ruling[u"Ruling"],
            }

            clean_data[u"TentativeRuling"].append(tentative_ruling)

        clean_data = clean_court_object(clean_data)

        return clean_data

    def _check_success(self, r):
        if r.json()["IsSuccess"]:
            self.case_data = r.text
            logger.info(u"Successful query into LASC map")
        else:
            logger.info(u"Failure to query into LASC map")
