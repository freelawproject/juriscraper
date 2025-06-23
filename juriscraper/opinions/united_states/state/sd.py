# Author: Michael Lissner
# History:
# - 2013-06-11: Birth.
# - 2013-08-06: Revised by Brian Carver
# - 2014-08-05: Updated URL by mlr
# - 2021-12-28: Updated by flooie
# - 2024-04-11: grossir, Merge backscraper and scraper; implement dynamic backscraper

import re
from datetime import datetime
from typing import Any

from juriscraper.AbstractSite import logger
from juriscraper.lib.html_utils import get_row_column_text
from juriscraper.lib.string_utils import titlecase
from juriscraper.OpinionSiteLinear import OpinionSiteLinear


class Site(OpinionSiteLinear):
    # data available in HTML format since 1996, in PDF since 2006
    start_year = 2006
    # judges full names from https://ujs.sd.gov/Supreme_Court/Justices.aspx
    initials_to_judges = {
        "MES": "Mark E. Salter",
        "SPM": "Scott P. Myren",
        "SRJ": "Steven R. Jensen",
        "PJD": "Patricia J. DeVaney",
        "JMK": "Janine M. Kern",
        # not current
        "JKM": "Judith Meierhenry",  # https://ujs.sd.gov/uploads/sc/opinions/24063.pdf
        "DG": "David Gilbertson",  # https://ujs.sd.gov/uploads/sc/opinions/23939.pdf
        "SLZ": "Steven L. Zinter",  # https://ujs.sd.gov/uploads/sc/opinions/24439.pdf
        "RWS": "Richard Sabers",  # https://ujs.sd.gov/uploads/sc/opinions/24501.pdf
        "JKK": "John Konenkamp",  # https://ujs.sd.gov/uploads/sc/opinions/24387.pdf
        "GAS": "Glen Severson",  # https://ujs.sd.gov/uploads/sc/opinions/25115.pdf
        "LSW": "Lori Wilbur",  # https://ujs.sd.gov/uploads/sc/opinions/25808.pdf
    }
    disposition_mapper = {
        "dismiss": "Dismissed",
        "dis": "Dismissed",  # https://ujs.sd.gov/uploads/sc/opinions/24312.pdf
        "a": "Affirmed",
        "r": "Reversed and remanded",
        "rev & rem": "Reverse and remanded",  # https://ujs.sd.gov/uploads/sc/opinions/24409.pdf
        "aff in pt & rev in pt": "Affirmed in part and reversed in part",
        "aff in pt, rev in pt & rem": "Affirmed in part, reversed in part and remanded",  # https://ujs.sd.gov/uploads/sc/opinions/23919.pdf
        "aff in pt, vacate, & rem in pt": "Affirmed in part, vacated and remanded in part",
        "aff in pt & vacate": "Affirmed and vacated",  # https://www.courtlistener.com/opinion/9502826/state-v-scott/pdf/
    }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.court_id = self.__module__
        self.url = "https://ujs.sd.gov/Supreme_Court/opinions.aspx"
        self.is_backscrape = False
        self.make_backscrape_iterable(kwargs)
        self.should_have_results = True

    def _process_html(self) -> None:
        """Parse HTML into case dictionaries

        :return None
        """
        for row in self.html.xpath("//tr[td/strong/a]"):
            title = get_row_column_text(row, 2)

            status = "Published"
            cite = re.findall(r"\d{4} S\.?D\.? \d+", title)
            if not cite:
                status = "Unpublished"
                cite = [""]

            url = row.xpath(".//a/@href")[0]
            docket = url.split("/")[-1][:5]
            name = titlecase(title.rsplit(",", 1)[0] if cite else title)
            self.cases.append(
                {
                    "date": get_row_column_text(row, 1),
                    "name": name,
                    "citation": cite[0],
                    "url": url,
                    "docket": docket,
                    "status": status,
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

    def _download_backwards(self, year: int) -> None:
        """Get input year's page

        We need to GET the homepage first to load hidden inputs
        Then, we can POST for the desired year's page

        :param year:
        :return: None
        """
        logger.info("Backscraping for year %s", year)
        self.is_backscrape = True

        self.method = "GET"
        self.html = super()._download()
        view_state = self.html.xpath("//input[@id='__VIEWSTATE']/@value")[0]
        event_validation = self.html.xpath(
            "//input[@id='__EVENTVALIDATION']/@value"
        )[0]
        a = self.html.xpath(
            f".//a[contains(@id,'ContentPlaceHolder1_ChildContent1_Repeater_OpinionsYear_LinkButton1')][contains(text(), '{year}')]/@href"
        )
        link = a[0].split("'")[1]
        data = {
            "__VIEWSTATE": view_state,
            "__EVENTVALIDATION": event_validation,
            "__EVENTTARGET": link,
        }
        self.parameters = data
        self.method = "POST"
        self.html = super()._download()
        self._process_html()

    def make_backscrape_iterable(self, kwargs: dict) -> None:
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

    def extract_from_text(self, scraped_text: str) -> dict[str, Any]:
        """Can we extract the date filed from the text?

        Some edge cases:
        - case with 2 judges https://www.courtlistener.com/opinion/9456271/mcgee-v-spencer-quarries-inc/pdf/
        - case without disposition:  https://www.courtlistener.com/opinion/10121701/discipline-of-ravnsborg/pdf/
        - case without a judge string https://www.courtlistener.com/opinion/9474051/in-the-matter-of-the-interpretation-of-south-dakota-constitution-and-state/pdf/

        :param scraped_text: The content of the document downloaded
        :return: Metadata to be added to the case
        """
        metadata = {}
        target_text = scraped_text[:100]

        dockets = re.findall(r"(?<=#)\d+", target_text)
        if dockets:
            metadata["Docket"] = {"docket_number": ", ".join(dockets)}

        judge_regex = r"-[A-Z]{2,3}(\s*[,&]\s+[A-Z]{2,3})*"
        if judges_match := re.search(judge_regex, target_text):
            initials = re.sub(r"[\s,&-]+", " ", judges_match.group(0)).strip()
            judges = []
            for initial in initials.split(" "):
                if judge := self.initials_to_judges.get(initial):
                    judges.append(judge)
                else:
                    # Catch updates
                    logger.error(
                        "Judge initials not mapped to full name %s", initial
                    )

            if judges:
                metadata["OpinionCluster"] = {"judges": ", ".join(judges)}

        disposition_regex = r"(?<=-)[a-z,&\s]+(?=-)"
        if disposition_match := re.search(disposition_regex, target_text):
            raw_disposition = disposition_match.group(0)
            if disp := self.disposition_mapper.get(raw_disposition):
                if metadata.get("OpinionCluster"):
                    metadata["OpinionCluster"]["disposition"] = disp
                else:
                    metadata["OpinionCluster"] = {"disposition": disp}

        return metadata
