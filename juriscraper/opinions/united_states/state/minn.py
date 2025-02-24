# Scraper for Minnesota Supreme Court
# CourtID: minn
# Court Short Name: MN
# Author: Andrei Chelaru
# Reviewer: mlr
# Date: 2014-07-03
# Contact:  Liz Reppe (Liz.Reppe@courts.state.mn.us), Jay Achenbach (jay.achenbach@state.mn.us)

# 2024-08-09: update and implement backscraper, grossir

import re
from datetime import date, datetime
from typing import Tuple
from urllib.parse import urljoin

from lxml import html
from urllib.parse import urlencode

from juriscraper.AbstractSite import logger
from juriscraper.OpinionSiteLinear import OpinionSiteLinear


class Site(OpinionSiteLinear):
    court_query = "supct"
    days_interval = 7
    first_opinion_date = date(1998, 1, 1)
    needs_special_headers = True

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.court_id = self.__module__

        self.status = "Published"
        if self.court_query == "ctapun":
            self.status = "Unpublished"

        self.base = "https://mn.gov/law-library/search/"
        self.params = self.base_params = {
            "v:sources": "mn-law-library-opinions",
            "query": f" (url:/archive/{self.court_query}) ",
            "sortby": "date",
        }
        self.request["verify"] = False
        self.request["headers"] = {
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Sec-Fetch-Site": "same-origin",
            "Sec-Fetch-Dest": "document",
            "Accept-Language": "en-US,en;q=0.9",
            "Sec-Fetch-Mode": "navigate",
            "Host": "mn.gov",
            "User-Agent": "Juriscraper/3.0 Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15",
            "Referer": "https://mn.gov/law-library/search/?v%3Asources=mn-law-library-opinions&query=+%28url%3A%2Farchive%2Fsupct%29+&citation=&qt=&sortby=&docket=&case=&v=&p=&start-date=&end-date=",
            "Connection": "keep-alive",
        }
        self.make_backscrape_iterable(kwargs)

    def _process_html(self) -> None:
        """Process the html and extract out the opinions

        :return: None
        """
        # self.html = self._download({"params": self.params})

        results_number = self.html.xpath(
            "//div[@class='searchresult_number']/text()"
        )
        if results_number:
            results_number = results_number[0].split(" of ")[-1].strip()
            if int(results_number) > 10:
                logger.warning(
                    "Page has a size 10, and there are %s results for this query",
                    results_number,
                )

        for case in self.html.xpath("//div[@class='searchresult']"):
            name = re.sub(r"\s+", " ", case.xpath(".//a/text()")[0])
            name_match = re.search(r"(?P<name>.+)\. A\d{2}-\d+", name)
            if name_match:
                name = name_match.group("name")

            summary = case.xpath(
                ".//div[@class='searchresult_snippet']/text()"
            )[0]
            disposition = ""
            # minnctapp_u sometimes has a disposition, but it's format
            # is much more variable
            if self.status == "Published":
                parts = summary.split(".")
                if (
                    len(parts) > 2
                    and len(parts[-2].split()) <= 10
                    and not re.search(r"\d", parts[-2])
                ):
                    # Sometimes there is no disposition. Ex: A23-1504
                    # False positives usually contain numbers. Ex: A22-0776
                    disposition = parts[-2].strip()

            raw_date = case.xpath(".//div[@class='searchresult_date']")[
                -1
            ].text_content()
            date_filed = re.sub(r"\s+", " ", raw_date).split(":")[1].strip()

            # Backscrapers may find citations, since they are attached some
            # months after the initial release of an opinion
            citation = ""
            if cite_element := case.xpath(
                ".//div[b[contains(text(), 'Citation:')]]"
            ):
                citation = (
                    cite_element[0].text_content().split(":", 1)[-1].strip()
                )

            url = case.xpath(".//a/@href")[0]
            docket = url.split("/")[-1].split("-")[0][2:]
            dock = f"{docket[:3]}-{docket[3:]}"
            self.cases.append(
                {
                    "date": date_filed,
                    "name": name,
                    "url": urljoin("https://", url),
                    "disposition": disposition,
                    "summary": summary,
                    "docket": [docket],
                    "citation": [citation],
                }
            )

    def _download_backwards(self, dates: Tuple[date]):
        count = 0
        logger.info("Backscraping for range %s - %s", *dates)
        while True:
            if(count<1):
                params = {**self.base_params}
                params.update(
                    {
                        "start-date": dates[0].strftime("%-m/%-d/%Y"),
                        "end-date": dates[1].strftime("%-m/%-d/%Y"),
                        "query": f"{params['query']}date:[{dates[0].strftime('%Y-%m-%d')}..{dates[1].strftime('%Y-%m-%d')}]",
                    }
                )
                self.url=f"{self.base}?{urlencode(params)}"
                count += 1

            else:
                link=self.html.xpath("//div[@class='results-navigation']/ul/li[last()]/a")
                if link:
                    self.url=link[0].xpath('.//@href')[0]
                else:
                    break

            print(f"hitting url {self.url}")
            self.html =self._download()
            self._process_html()


    def crawling_range(self, start_date: datetime, end_date: datetime) -> int:
        start_date=datetime(2024,1,1,)
        end_date=datetime(2024,12,31)
        self._download_backwards((start_date,end_date))

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

    def get_court_type(self):
        return "state"

    def get_class_name(self):
        return "minn"

    def get_state_name(self):
        return "Minnesota"

    def get_court_name(self):
        return "Supreme Court of Minnesota"
