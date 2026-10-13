"""Scraper for United States District Court for the District of Columbia
CourtID: dcd
Court Short Name: D.D.C.
Author: V. David Zvenyach
Date created: 2014-02-27
Substantially Revised: Brian W. Carver, 2014-03-28
"""

import re
import time
from datetime import date

from lxml import html
from lxml.html import HtmlElement
from typing_extensions import Unpack, override

from juriscraper.AbstractSite import SiteOptions
from juriscraper.lib.string_utils import CaseNameTweaker, titlecase
from juriscraper.OpinionSite import OpinionSite


class Site(OpinionSite):
    def __init__(
        self,
        cnt: CaseNameTweaker | None = None,
        user_agent: str = "Juriscraper",
        **kwargs: Unpack[SiteOptions],
    ) -> None:
        super().__init__(cnt, user_agent, **kwargs)
        self.court_id = self.__module__
        self.url = "https://ecf.dcd.uscourts.gov/cgi-bin/Opinions.pl?2013"

    @override
    def _get_download_urls(self) -> list[str]:
        # There are often multiple documents and hence urls for each case.
        # This requires us to pad every other metadata field to match the
        # number of urls we find here.
        path = "//table[2]//tr[position()>0]/td[3]/a/@href"
        if not isinstance(self.html, HtmlElement):
            raise ValueError(
                "An HTML document must be downloaded before parsing."
            )
        texts: list[str] = self.html.xpath(path)
        return texts

    @override
    def _get_case_names(self) -> list[str]:
        casenames = []
        rowpath = "//table[2]//tr[position()>0]"
        cnpath = "./td[2]//text()[preceding-sibling::br]"
        urlpath = "./td[3]/a/@href"
        if not isinstance(self.html, HtmlElement):
            raise ValueError(
                "An HTML document must be downloaded before parsing."
            )
        rows: list[HtmlElement] = self.html.xpath(rowpath)
        for row in rows:
            case_list: list[str] = row.xpath(cnpath)
            for rough_case_name in case_list:
                case_name = titlecase(rough_case_name.lower())
                # Determine the number of urls in each row and pad the case
                # name list sufficiently
                count = len(row.xpath(urlpath))
                casenames.extend([case_name] * count)
        return casenames

    @override
    def _get_case_dates(self) -> list[date]:
        dates = []
        rowpath = "//table[2]//tr[position()>0]"
        datepath = "./td[1]/text()"
        urlpath = "./td[3]/a/@href"
        if not isinstance(self.html, HtmlElement):
            raise ValueError(
                "An HTML document must be downloaded before parsing."
            )
        rows: list[HtmlElement] = self.html.xpath(rowpath)
        for row in rows:
            date_string: list[str] = row.xpath(datepath)
            for d in date_string:
                date_object = date.fromtimestamp(
                    time.mktime(time.strptime(d, "%m/%d/%Y"))
                )
                # Determine the number of urls in each row and pad the date
                # list sufficiently
                count = len(row.xpath(urlpath))
                dates.extend([date_object] * count)
        return dates

    @override
    def _get_precedential_statuses(self) -> list[str]:
        return ["Published"] * len(self)

    @override
    def _get_docket_numbers(self) -> list[str]:
        docket_numbers = []
        rowpath = "//table[2]//tr[position()>0]"
        dktpath = "./td[2]//text()[following-sibling::br]"
        urlpath = "./td[3]/a/@href"
        if not isinstance(self.html, HtmlElement):
            raise ValueError(
                "An HTML document must be downloaded before parsing."
            )
        rows: list[HtmlElement] = self.html.xpath(rowpath)
        for row in rows:
            docket_number: list[str] = row.xpath(dktpath)
            # Determine the number of urls in each row and pad the docket
            # numbers list sufficiently
            count = len(row.xpath(urlpath))
            docket_numbers.extend(docket_number * count)
        return docket_numbers

    @override
    def _get_docket_document_numbers(self) -> list[str]:
        document_numbers = []
        regex = re.compile(r"(\?)(\d+)([a-z]+)(\d+)(-)(.*)")
        if not isinstance(self.html, HtmlElement):
            raise ValueError(
                "An HTML document must be downloaded before parsing."
            )
        urls: list[str] = self.html.xpath(
            "//table[2]//tr[position()>0]/td[3]/a/@href"
        )
        for url in urls:
            # Because we are acting directly on the entire url list, no padding
            # of the docket number field is required.
            doc_no = regex.search(url)
            # In 2012 (and perhaps elsewhere) they have a few weird urls.
            if doc_no is not None:
                document_numbers.append(doc_no.group(6))
            else:
                document_numbers.append(url)
        return document_numbers

    @override
    def _get_judges(self) -> list[str]:
        judges = []
        rowpath = "//table[2]//tr[position()>0]"
        urlpath = "./td[3]/a/@href"
        judgepath = "./td[3]"
        if not isinstance(self.html, HtmlElement):
            raise ValueError(
                "An HTML document must be downloaded before parsing."
            )
        rows: list[HtmlElement] = self.html.xpath(rowpath)
        for row in rows:
            judge_elements: list[HtmlElement] = row.xpath(judgepath)
            for judge_element in judge_elements:
                judge_string = html.tostring(
                    judge_element, method="text", encoding="unicode"
                )
                match = re.search(r"(by\s)(.*)", judge_string, re.MULTILINE)
                if match is None:
                    raise ValueError(
                        f"Could not parse opinion judge: {judge_string!r}"
                    )
                judge = match.group(2)
                # Determine the number of urls in each row and pad the judges
                # list sufficiently
                count = len(row.xpath(urlpath))
                judges.extend([judge] * count)
        return judges

    @override
    def _get_nature_of_suit(self) -> list[str]:
        nos = []
        if not isinstance(self.html, HtmlElement):
            raise ValueError(
                "An HTML document must be downloaded before parsing."
            )
        urls: list[str] = self.html.xpath(
            "//table[2]//tr[position()>0]/td[3]/a/@href"
        )
        for url in urls:
            # Because we are acting directly on the entire url list, no padding
            # of the nature of suit field is required.
            url_str = re.search(r"(\?)(\d+)([a-z]+)(\d+)(-)(.*)", url)
            # In 2012 (and perhaps elsewhere) they have a few weird urls.
            if url_str is not None:
                nature_code = url_str.group(3)
                if nature_code == "cv":
                    nos.append("Civil")
                elif nature_code == "cr":
                    nos.append("Criminal")
                # This is a tough call. Magistrate Cases are typically also
                # Criminal or Civil cases, and their docket_number field will
                # reflect this, but they do classify these separately under
                # these 'mj' and 'mc' codes and the first page of these
                #  documents will often refer to them as 'Magistrate Case
                # ####-####' so, we will too.
                elif nature_code in ("mj", "mc"):
                    nos.append("Magistrate Case")
                else:
                    nos.append("Unknown")
            else:
                nos.append("Unknown")
        return nos
