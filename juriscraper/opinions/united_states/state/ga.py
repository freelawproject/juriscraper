#  Scraper for Georgia Supreme Court
# CourtID: ga
# Court Short Name: ga

import re
from datetime import date

from juriscraper.AbstractSite import logger
from juriscraper.lib.exceptions import InsanityException
from juriscraper.lib.string_utils import titlecase
from juriscraper.OpinionSiteLinear import OpinionSiteLinear


class Site(OpinionSiteLinear):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.court_id = self.__module__
        self.url = self._get_url(date.today().year)
        self.status = "Published"
        self.back_scrape_iterable = range(2016, 2022)
        self.regex_docket = re.compile(r"(S?[0-9]{2}[A-Z]{1}[0-9]{4})")

    def _get_url(self, year: int) -> str:
        return "https://www.gasupreme.us/opinions/%d-opinions/" % year

    def _process_html(self):
        paths = "//p/strong | //p/b | //p/font/strong | //p/font/b"
        for date_element in self.html.xpath(paths):
            string = date_element.xpath("./text()")
            try:
                string = string[0]
                # handle examples where time but no date (ga_example_3.html)
                if ":" in string and ("AM" in string or "PM" in string):
                    continue
                # handle legacy example (ga_example.html)
                string = string.split("SUMMARIES")[0]
                date_string = re.sub(r"\W+", " ", string)
                # handle legacy example (ga_example.html)
                if len(date_string.split()) != 3:
                    continue
            except:
                continue
            parent = date_element.xpath("./..")[0]
            # handle legacy example (ga_example.html)
            while parent.tag != "p":
                parent = parent.xpath("./..")[0]
            for item in parent.getnext().xpath("./li"):
                text = item.text_content()
                if text:
                    # Extract Docket numbers
                    dockets = re.findall(self.regex_docket, text)
                    if not dockets:
                        if (
                            text
                            == "IN RE: MOTION TO AMEND 2021-3 (Bar Rule 1.2)"
                        ):
                            continue
                        else:
                            raise InsanityException(
                                f"Could not find docket numbers in: '{text}'"
                            )

                    # Extract name substring; I am sure this could
                    # be done with a more slick regex, but its not
                    # my forte...
                    name = text
                    for docket in dockets:
                        name = name.replace(docket, "")
                    name = name.lstrip(" .,")

                    self.cases.append(
                        {
                            "date": date_string,
                            "docket": ", ".join(dockets),
                            "name": titlecase(name.lstrip(" .,")),
                            "url": item.xpath(".//a[1]/@href")[0],
                        }
                    )

    def _download_backwards(self, year):
        self.url = self._get_url(year)
        logger.info(f"Backscraping for year {year}: {self.url}")
        self.html = self._download()

        # Setting status is important because it prevents the download
        # function from being run a second time by the parse method.
        if self.html is not None:
            self.status = 200
            self._process_html()
