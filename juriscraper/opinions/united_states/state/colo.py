"""Scraper for Colorado Supreme Court
CourtID: colo
Court Short Name: Colo.
Author: Philip Ardery
Reviewer: mlr
Date created: 2016-06-03
History:
    - 2022-01-31: Updated by William E. Palin
    - 2023-01-05: Updated by WEP
    - 2023-11-19: Drop Selenium by WEP
    - 2023-12-20: Updated with citations, judges and summaries, Palin
"""

import datetime
import re
from datetime import date, timedelta
from typing import Any, Dict

from dateutil import parser

from juriscraper.OpinionSiteLinear import OpinionSiteLinear


class Site(OpinionSiteLinear):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.court_id = self.__module__
        self.status = "Published"
        self.url = "https://www.courts.state.co.us/Courts/Supreme_Court/Proceedings/Index.cfm"

    def _process_html(self):
        """"""
        for row in self.html.xpath("//div[@id='Dispositions']/a"):
            case_id = row.attrib["onclick"].split("'")[1]
            div = row.xpath(f"//div[@id='Case_{case_id}']")[0]
            if not div.xpath(".//a/text()"):
                # This is set to avoid data decades back
                continue
            document_type = div.xpath(".//a/text()")[0]
            if "Opinion" not in document_type:
                # Only collect opinions and not orders
                continue
            summary = (
                row.xpath(f"//div[@id='Case_{case_id}']")[0]
                .text_content()
                .strip()
            )
            url = div.xpath(".//a/@href")[0]
            title = row.xpath("following-sibling::text()")[0].strip()
            docket, name = title.split(" ", 1)
            name, _ = name.split("  ")
            if "(Honorable" in name:
                name, judge = name.split("(")
                name = name.strip()
                judges = judge.strip(")").strip().replace("Honorable", "")
            else:
                judges = ""
            date_filed = self.find_date(summary)
            if parser.parse(date_filed).date() < self.set_min_date():
                # Only collect back 6 months
                break
            if "https://www.courts.state.co.us/" not in url:
                url = f"https://www.courts.state.co.us/{url}"
            self.cases.append(
                {
                    "summary": summary,
                    "date": date_filed,
                    "name": name,
                    "docket": docket.strip(","),
                    "url": url,
                    "judge": judges,
                }
            )

    def set_min_date(self):
        """Set minimum date to add opinions

        :return: Date 6 months back
        """
        if self.test_mode_enabled():
            today = datetime.date(2023, 11, 19)
            return today - timedelta(180)
        else:
            return date.today() - timedelta(180)

    def find_date(self, summary) -> str:
        """Find date filed

        Normally it follows a typical pattern but not always

        :param summary: Use summary text to find date filed
        :return: date as string
        """
        if "Opinion issued" in summary:
            return summary.split("Opinion issued")[1]
        date_pattern = re.compile(
            r"((January|February|March|April|May|June|July|August|September|October|November|December)\s+(\d{1,2})\s?,?\s+(\d{4}))"
        )
        match = re.findall(date_pattern, summary)
        date_filed = match[-1][0] if match else ""
        return date_filed

    def extract_from_text(self, scraped_text: str) -> Dict[str, Any]:
        """Extract Citation from text

        :param scraped_text: Text of scraped content
        :return: date filed
        """
        m = re.findall(r"(20\d{2})\s(CO)\s(\d+A?)", scraped_text)
        if m:
            vol, reporter, page = m[0]
            return {
                "Citation": {
                    "volume": vol,
                    "reporter": reporter,
                    "page": page,
                    "type": 8,  # NEUTRAL in courtlistener Citation model
                },
            }
        return {}
