"""Scraper for Louisiana Court of Appeal, First Circuit
CourtID: lactapp_1
Court Short Name: La. Ct. App. 1st Cir.
Author: mmantel
History:
  2019-11-24: Created by mmantel
  2025-07-21: Updated by quevon24
"""

import json
import re
from datetime import datetime

from juriscraper.AbstractSite import logger
from juriscraper.OpinionSiteLinear import OpinionSiteLinear


class Site(OpinionSiteLinear):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.court_id = self.__module__
        self.status = "Unknown"
        self.base_url = "https://lafcca.hosted2.civiclive.com/portal/svc/ContentItemSvc.asmx/GetItemList"
        self.url = self.base_url
        self.method = "POST"
        self.should_have_results = True

        if datetime.now().year != 2025:
            logger.error("Update lactapp_1 parameters from 2025 parameters")

        # This payload is specific for 2025
        self.payload = {
            "parentId": "283468",
            "Params": json.dumps(
                {
                    "ContextId": 283467,
                    "OneLink": "/cms/One.aspx",
                    "RawUrl": "/cms/One.aspx?portalId=161585&pageId=283465",
                    "Extension": "23741",
                    "PortalId": "161585",
                    "PageId": "283465",
                    "InstanceId": "23741",
                }
            ),
        }

        self.parameters = json.dumps(self.payload)

        self.request["headers"] = {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "User-Agent": "Juriscraper",
        }

    def _download(self, request_dict=None):
        if self.test_mode_enabled():
            return super()._download(request_dict)

        self._request_url_post(self.url)
        self._post_process_response()
        return self._return_response_text_object()

    @staticmethod
    def extract_case_name_info(case_name):
        """Extracts docket number and cleans case name

        :param case_name: raw case name with docket number
        :return: (docket_number, clean_name)
        """
        # Match pattern: YYYY XX #### (4 digits year, 2 letters, 4 digits)
        # e.g. 2025 KW 0712, 2025 KM 0194, 2025 KA 0031, 2025 CW 0606, 2025 CJ 0045, 2025 CA 0022
        match = re.match(r"^(\d{4}\s[A-Z]{2}\s\d{4})\s+(.*)", case_name)
        if match:
            return match.group(1), match.group(2).strip()
        return None, case_name  # Return original name if no docket found

    def _process_html(self):
        json_data = self.html
        for item in json_data["d"]["DataObject"]:
            docket, clean_name = self.extract_case_name_info(item["Name"])
            case = {
                "name": clean_name,
                "url": item["DownloadLink"],
                "date": item["CreationDateString"],
                "docket": docket,
                "status": self.status,
            }
            self.cases.append(case)
