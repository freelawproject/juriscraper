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

from pydantic import TypeAdapter
from typing_extensions import TypedDict, Unpack, override

from juriscraper.AbstractSite import (
    DownloadedContent,
    RequestParameters,
    SiteOptions,
    logger,
)
from juriscraper.lib.string_utils import CaseNameTweaker
from juriscraper.lib.type_utils import RawOpinion
from juriscraper.OpinionSiteLinear import OpinionSiteLinear


class _Item(TypedDict):
    Name: str
    DownloadLink: str
    CreationDateString: str


class _Data(TypedDict):
    DataObject: list[_Item]


class _Response(TypedDict):
    d: _Data


_response_adapter = TypeAdapter(_Response)


class Site(OpinionSiteLinear):
    def __init__(
        self,
        cnt: CaseNameTweaker | None = None,
        user_agent: str = "Juriscraper",
        **kwargs: Unpack[SiteOptions],
    ) -> None:
        super().__init__(cnt, user_agent, **kwargs)
        self.court_id = self.__module__
        self.status = "Unknown"
        self.base_url = "https://lafcca.hosted2.civiclive.com/portal/svc/ContentItemSvc.asmx/GetItemList"
        self.url = self.base_url
        self.method = "POST"
        self.should_have_results = True

        if datetime.now().year != 2026:
            logger.error("Update lactapp_1 parameters from 2026 parameters")

        # This payload is specific for 2026
        self.payload = {
            "parentId": "310729",
            "Params": json.dumps(
                {
                    "ContextId": 310728,
                    "OneLink": "/cms/One.aspx",
                    "RawUrl": "/decisions/o_p_i_n_i_o_n_s_2026",
                    "Extension": "24725",
                    "PortalId": "161585",
                    "PageId": "310727",
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

    @override
    async def _download(
        self, request_dict: RequestParameters | None = None
    ) -> DownloadedContent:
        if self.test_mode_enabled():
            return await super()._download(request_dict)

        if self.url is None:
            raise ValueError("The opinion API URL is not configured")
        await self._request_url_post(self.url)
        self._post_process_response()
        return self._return_response_text_object()

    @staticmethod
    def extract_case_name_info(case_name: str) -> tuple[str | None, str]:
        """Extracts docket number and cleans case name

        :param case_name: raw case name with docket number
        :return: (docket_number, clean_name)
        """
        # Match pattern: YYYY XX #### (4 digits year, 2 letters, 4 digits)
        # e.g. 2025 KW 0712, 2025 KM 0194, 2025 KA 0031, 2025 CW 0606, 2025 CJ 0045, 2025 CA 0022
        match = re.match(r"^(\d{4}\s[A-Z]{2}\s\d{4})\s+(.*)", case_name)
        if match is not None:
            return match.group(1), match.group(2).strip()
        return None, case_name  # Return original name if no docket found

    @override
    def _process_html(self) -> None:
        json_data = _response_adapter.validate_python(self.html, strict=True)
        for item in json_data["d"]["DataObject"]:
            docket, clean_name = self.extract_case_name_info(item["Name"])
            case: RawOpinion = {
                "name": clean_name,
                "url": item["DownloadLink"],
                "date": item["CreationDateString"],
                "docket": docket,
                "status": self.status,
            }
            self.cases.append(case)
