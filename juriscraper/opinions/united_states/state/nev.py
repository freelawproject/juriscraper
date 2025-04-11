"""Scraper for Nevada Supreme Court
CourtID: nev

History:
    - 2023-12-13: Updated by William E. Palin
"""

import json
from datetime import datetime
from juriscraper.AbstractSite import logger
from juriscraper.OpinionSiteLinear import OpinionSiteLinear


class Site(OpinionSiteLinear):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.court_id = self.__module__
        self.url = "https://publicaccess.nvsupremecourt.us/WebSupplementalAPI/api/AdvanceOpinions"
        self.pdfurl = "https://publicaccess.nvsupremecourt.us/WebSupplementalAPI/api/urlRequest/doc/"
        self.status = "Published"
        self.court_code = "10001"
        self.headers = {
            "Referer": "https://nvcourts.gov/",
            "XApiKey": "080d4202-61b2-46c5-ad66-f479bf40be11",
            # "Origin":"https://nvcourts.gov/"
        }
        self.filtered_json=[]

    def _download(self, **kwargs):
        """Download the JSON to parse

        :param kwargs:
        :return: None
        """
        logger.info(f"Now downloading case page at: {self.url}")
        if self.test_mode_enabled():
            return json.load(open(self.url))
        return (

            self.request["session"]
            .get(
                self.url,
                headers=self.headers,
            )
            .json()
        )

    def filter_cases(self):
        """Filter JSON to last two opinions without dupes

        Consolidated cases get listed multiple times so we want to remove
        those as well to avoid duplication issues

        :return: List of cases to download
        """
        cases = []
        for case in self.filtered_json:
            advances = [case["advanceNumber"] for case in cases]
            if (
                "COA" in case["caseNumber"]
                or case["advanceNumber"] in advances
            ):
                continue
            cases.append(case)
        return cases

    def _process_html(self):
        """Process Nevada Case Opinions

        :return: None
        """
        fil_cases = self.filter_cases()

        for case in fil_cases:
            logger.info(f"fetching the details of the case with docket : {case['caseNumber']}")

            self.docurl=case['caseTitle']
            vol = int(case["date"].split("-")[0]) - 1884
            citation = f"{vol} Nev., Advance Opinion {case['advanceNumber']}"

            if len(case['caseTitle'].strip().split("C/W"))==1:
                name = case['caseTitle'].strip()
                docket = [case['caseNumber']]
            else:
                name = case['caseTitle'].split("C/W")[0].strip()
                docket = [case['caseNumber']]
                docket = docket + case['caseTitle'].strip().split("C/W")[1].strip().split("/")

            pdf_url = self.get_pdf_url(case['docurl'])

            self.cases.append(
                {
                    "citation": [citation],
                    "name": name,
                    "docket": docket,
                    "date": case['date'],
                    "url": pdf_url,
                }
            )

    def get_pdf_url(self,dourl : str):
        u=f"{self.pdfurl}%20{dourl}"
        url_json = self.request["session"].get(u,headers=self.headers).json()
        return url_json['value']

    def filter_records_by_date_range(self,data, start_date: datetime, end_date: datetime):

        filtered_records = [
            record for record in data
            if start_date <= datetime.strptime(record["date"],
                                               "%Y-%m-%dT%H:%M:%S") <= end_date
        ]
        return filtered_records

    def crawling_range(self, start_date: datetime, end_date: datetime) -> int:
        if not self.downloader_executed:
            self.html = self._download()
            self.filtered_json = self.filter_records_by_date_range(self.html, start_date, end_date)

            self._process_html()

        for attr in self._all_attrs:
            self.__setattr__(attr, getattr(self, f"_get_{attr}")())

        self._clean_attributes()
        if "case_name_shorts" in self._all_attrs:
            self.case_name_shorts = self._get_case_name_shorts()
        self._post_parse()
        self._check_sanity()
        self._date_sort()
        self._make_hash()
        return len(self.cases)

    def get_class_name(self):
        return "nev"

    def get_court_name(self):
        return "Supreme Court of Nevada"

    def get_state_name(self):
        return "Nevada"

    def get_court_type(self):
        return "state"
