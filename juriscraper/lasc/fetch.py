from datetime import datetime, timedelta

from dateutil.rrule import WEEKLY, rrule

from ..lib.log_tools import make_default_logger
from ..lib.utils import clean_court_object

logger = make_default_logger()


class LASCSearch:
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
            f"https://{self.api_base}GetCaseDetail/{internal_case_id}"
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
        date_query_url = "https://{}GetRecentCivilCases/{}/{}".format(
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

        logger.info("Api ViewDocument called.  Downloading PDF ")
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
            "Parsing lasc data from returned JSON into normalized " "format"
        )

        try:
            data = case_data["ResultList"][0]["NonCriminalCaseInformation"]
        except IndexError:
            # Some cases don't have any data at all, see: P4160;JCC;CV. When
            # this happens, Juriscraper returns nothing as well.
            return {}

        # Docket Normalization
        clean_data = {"QueuedCase": [], "LASCPDF": [], "LASCJSON": []}

        case_info = data["CaseInformation"]

        docket = {
            "date_filed": case_info["FilingDate"].date(),
            "date_disposition": None,
            "docket_number": case_info["CaseNumber"],
            "district": case_info["District"],
            "division_code": case_info["DivisionCode"],
            "disposition_type": case_info["DispositionType"],
            "disposition_type_code": "",
            "case_type_str": case_info["CaseTypeDescription"],
            "case_type_code": case_info["CaseType"],
            "case_name": case_info["CaseTitle"] or "",
            "judge_code": "",
            "judge_name": case_info["JudicialOfficer"],
            "courthouse_name": case_info["Courthouse"],
        }

        if case_info["StatusDate"] is not None:
            docket["date_status"] = datetime.strptime(
                case_info["StatusDate"], "%m/%d/%Y"
            ).date()
        else:
            docket["date_status"] = case_info["StatusDate"]

        docket["status_code"] = case_info["StatusCode"] or ""
        docket["status_str"] = case_info["Status"]
        clean_data["Docket"] = docket

        # Register of Actions normalization
        clean_data["Action"] = []
        for action in data["RegisterOfActions"]:
            registered_action = {
                "date_of_action": action["RegisterOfActionDate"],
                "description": action["Description"],
                "additional_information": action["AdditionalInformation"],
            }
            clean_data["Action"].append(registered_action)

        # Cross References normalization
        clean_data["CrossReference"] = []
        for cross_ref in data["CrossReferences"]:
            cross_reference = {
                "date_cross_reference": cross_ref["CrossReferenceDate"],
                "cross_reference_docket_number": cross_ref[
                    "CrossReferenceCaseNumber"
                ]
                or "",
                "cross_reference_type": cross_ref[
                    "CrossReferenceTypeDescription"
                ],
            }
            clean_data["CrossReference"].append(cross_reference)

        # Documents Filed
        clean_data["DocumentFiled"] = []
        for doc_filed in data["DocumentsFiled"]:
            document = {
                "date_filed": doc_filed["DateFiled"],
                "memo": doc_filed["Memo"] or "",
                "document_type": doc_filed["Document"] or "",
                "party_str": doc_filed["Party"] or "",
            }
            clean_data["DocumentFiled"].append(document)

        clean_data["QueuedPDF"] = []
        clean_data["DocumentImage"] = []
        for doc_image in data["DocumentImages"]:
            image = {
                "date_processed": doc_image["createDate"],
                "date_filed": doc_image["docFilingDate"],
                "doc_id": doc_image["docId"],
                "page_count": doc_image["pageCount"],
                "document_type": doc_image["documentType"] or "",
                "document_type_code": doc_image["documentTypeID"],
                "image_type_id": doc_image["imageTypeId"],
                "app_id": doc_image["appId"] or "",
                "odyssey_id": doc_image["OdysseyID"] or "",
                "is_downloadable": doc_image["IsDownloadable"],
                "security_level": doc_image["securityLevel"],
                "description": doc_image["description"] or "",
                "doc_part": doc_image["docPart"] or "",
                "is_available": False,
            }

            pdf_queue = {
                "internal_case_id": data["CaseInformation"]["CaseID"],
                "document_id": doc_image["docId"],
            }

            clean_data["DocumentImage"].append(image)
            clean_data["QueuedPDF"].append(pdf_queue)

        clean_data["Party"] = []
        for party in data["Parties"]:
            party_obj = {
                "attorney_name": party["AttorneyName"],
                "attorney_firm": party["AttorneyFirm"],
                "entity_number": party["EntityNumber"],
                "party_name": party["Name"],
                "party_flag": party["PartyFlag"],
                "party_type_code": party["PartyTypeCode"] or "",
                "party_description": party["PartyDescription"] or "",
            }
            clean_data["Party"].append(party_obj)

        clean_data["Proceeding"] = []
        for proceeding in data["PastProceedings"]:
            event = {
                "past_or_future": 1,
                "date_proceeding": proceeding["ProceedingDate"],
                "proceeding_time": proceeding["ProceedingTime"],
                "proceeding_room": proceeding["ProceedingRoom"],
                "am_pm": proceeding["AMPM"],
                "memo": proceeding["Memo"],
                "courthouse_name": proceeding["CourthouseName"],
                "address": proceeding["Address"],
                "result": proceeding["Result"],
                "judge_name": proceeding["Judge"],
                "event": proceeding["Event"],
            }
            clean_data["Proceeding"].append(event)

        for proceeding in data["FutureProceedings"]:
            event = {
                "past_or_future": 2,
                "date_proceeding": proceeding["ProceedingDate"],
                "proceeding_time": proceeding["ProceedingTime"],
                "proceeding_room": proceeding["ProceedingRoom"],
                "am_pm": proceeding["AMPM"],
                "memo": proceeding["Memo"],
                "courthouse_name": proceeding["CourthouseName"],
                "address": proceeding["Address"],
                "result": proceeding["Result"],
                "judge_name": proceeding["Judge"],
                "event": proceeding["Event"],
            }
            clean_data["Proceeding"].append(event)

        clean_data["TentativeRuling"] = []
        for ruling in data["TentativeRulings"]:
            tentative_ruling = {
                "date_created": ruling["CreationDate"],
                "date_hearing": ruling["HearingDate"],
                "department": ruling["Department"],
                "ruling": ruling["Ruling"],
            }

            clean_data["TentativeRuling"].append(tentative_ruling)

        clean_data = clean_court_object(clean_data)

        return clean_data

    def _check_success(self, r):
        if r.json()["IsSuccess"]:
            self.case_data = r.text
            logger.info("Successful query into LASC map")
        else:
            logger.info("Failure to query into LASC map")
