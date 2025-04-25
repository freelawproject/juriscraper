# Author: Michael Lissner
# History:
# - 2013-06-11: Birth.
# - 2013-08-06: Revised by Brian Carver
# - 2014-08-05: Updated URL by mlr
# - 2021-12-28: Updated by flooie
# - 2024-04-11: grossir, Merge backscraper and scraper; implement dynamic backscraper

import re
from datetime import datetime
from typing import Any, Dict

from lxml import html

from juriscraper.AbstractSite import logger
from juriscraper.lib.html_utils import get_row_column_text
from juriscraper.lib.string_utils import titlecase
from juriscraper.OpinionSiteLinear import OpinionSiteLinear


class Site(OpinionSiteLinear):
    start_year = 1996

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.court_id = self.__module__
        self.status = "Published"
        self.base = "https://ujs.sd.gov/supreme-court/opinions/"
        self.is_backscrape = False
        self.make_backscrape_iterable(kwargs)

    def _fetch_duplicate(self, data):
        # Create query for duplication
        query_for_duplication = {"pdf_url": data.get("pdf_url"),
                                 "docket": data.get("docket"),
                                 "title": data.get("title")}
        # Find the document
        query_for_url = {
                                 "docket": data.get("docket"),
                                 "title": data.get("title")}
        duplicate = self.judgements_collection.find_one(query_for_duplication)
        url_d = self.judgements_collection.find_one(query_for_url)

        url=url_d["pdf_url"]
        object_id = None
        if duplicate is None:
            if data.get("pdf_url").split('/')[-1] in url.split('/')[-1]:
                processed = url_d.get("processed")
                if processed == 10:
                    raise Exception(
                        "Judgment already Exists!")  # Replace with your custom DuplicateRecordException
                else:
                    object_id = url_d.get(
                        "_id")
            else:
                # Insert the new document
                self.judgements_collection.insert_one(data)

                # Retrieve the document just inserted
                updated_data = self.judgements_collection.find_one(
                    query_for_duplication)
                object_id = updated_data.get(
                    "_id")  # Get the ObjectId from the document
                self.flag = True
        else:
            # Check if the document already exists and has been processed
            processed = duplicate.get("processed")
            if processed == 10:
                raise Exception(
                    "Judgment already Exists!")  # Replace with your custom DuplicateRecordException
            else:
                object_id = duplicate.get(
                    "_id")  # Get the ObjectId from the existing document
        return object_id
    def _process_html(self) -> None:

        for row in self.html.xpath(".//table[@class='file-search-results__table']/tbody/tr"):
            title = row.xpath(".//td[2]//a/text()")[0]
            name = re.sub(r',\s*\d{4}\s*S\.D\.\s*\d+', '',title)
            cite = re.findall(r"\d{4} S\.D\. \d+", title)
            if not cite:
                continue

            # https://ujs.sd.gov/uploads/sc/opinions/2928369ef9a6.pdf
            # We abstract out the first part of the docket number here
            # And process the full docket number in the `extract_from_text` method
            # Called after the file has been downloaded.
            url = row.xpath(".//td[2]//a/@href")[0]
            docket = url.split("/")[-1][:5]
            self.cases.append(
                {
                    "date": get_row_column_text(row, 1),
                    "name": titlecase(title.rsplit(",", 1)[0]),
                    "citation": cite,
                    "url": url,
                    "docket": [docket],
                }
            )

        if self.is_backscrape:
            page_count = self.html.xpath(
                "//span[@id='ContentPlaceHolder1_ChildContent1_Label_Page']"
            )[0].text_content()
            page_of = re.findall(r"Page (\d+) of (\d+)", page_count)

            if len(set(page_of[0])) == 1:
                return

            logger.info(
                "Getting page %s of %s", int(page_of[0][0]) + 1, page_of[0][1]
            )
            self.get_next_page()
            self._process_html()

    def get_next_page(self) -> None:
        """Gets next page"""
        view_state = self.html.xpath("//input[@id='__VIEWSTATE']/@value")[0]
        event_validation = self.html.xpath(
            "//input[@id='__EVENTVALIDATION']/@value"
        )[0]
        data = {
            "ctl00$ctl00$ScriptManager1": "ctl00$ctl00$ContentPlaceHolder1$ChildContent1$UpdatePanel_Opinions|ctl00$ctl00$ContentPlaceHolder1$ChildContent1$LinkButton_Next",
            "__EVENTTARGET": "ctl00$ctl00$ContentPlaceHolder1$ChildContent1$LinkButton_Next",
            "__VIEWSTATE": view_state,
            "__EVENTVALIDATION": event_validation,
        }
        self.parameters = data
        self.html = super()._download()

    def make_backscrape_iterable(self, kwargs: Dict) -> None:
        """Creates backscrape iterable from kwargs or defaults

        :param kwargs: passed when initializing the scraper, may or
            may not contain backscrape controlling arguments
        :return None
        """
        start = kwargs.get("backscrape_start")
        end = kwargs.get("backscrape_end")

        start = int(start) if start else self.start_year
        end = int(end) + 1 if end else datetime.today().year

        self.back_scrape_iterable = range(start, end)

    def extract_from_text(self, scraped_text: str) -> Dict[str, Any]:
        """Can we extract the date filed from the text?

        :param scraped_text: The content of the document downloaded
        :return: Metadata to be added to the case
        """

        # The docket number appears to be the first text on the page.
        # So I crop the text to avoid any confusion that might occur in the
        # body of an opinion.
        docket = re.findall(r"#\d+.*-.-\w{3}", scraped_text[:100])[0]
        metadata = {
            "Docket": {
                "docket_number": docket,
            },
        }
        return metadata

    def crawling_range(self, start_date: datetime, end_date: datetime) -> int:
        sy = start_date.year
        es = end_date.year
        print(f"start and end year is {sy} , {es}")
        while sy <= es:
            print(f"for the year {sy}")
            page = 1
            while True:
                self.url = f"{self.base}/?year={sy}&page={page}"
                page += 1
                self.html=self._download()

                html_string = html.tostring(self.html,
                                            ).decode('UTF-8')
                if "We're sorry, there were no results found for this search." in html_string: break
                self._process_html()

            sy +=1

        for attr in self._all_attrs:
            self.__setattr__(attr, getattr(self, f"_get_{attr}")())

        self._clean_attributes()
        if "case_name_shorts" in self._all_attrs:
            # This needs to be done *after* _clean_attributes() has been run.
            # The current architecture means this gets run twice. Once when we
            # iterate over _all_attrs, and again here. It's pretty cheap though.
            self.case_name_shorts = self._get_case_name_shorts()
        self._post_parse()
        self._check_sanity()
        self._date_sort()
        self._make_hash()
        return len(self.cases)

    def get_class_name(self):
        return "sd"

    def get_court_name(self):
        return "Supreme Court of South Dakota"

    def get_court_type(self):
        return "state"

    def get_state_name(self):
        return "South Dakota"
