"""
Scraper for Florida 1st District Court of Appeals
CourtID: fladistctapp1
"""

from datetime import datetime, timedelta
from urllib.parse import urlencode, urljoin

from PIL.ImImagePlugin import number

from juriscraper.AbstractSite import logger
from juriscraper.lib.string_utils import titlecase
from juriscraper.OpinionSiteLinear import OpinionSiteLinear


class Site(OpinionSiteLinear):
    court_index = "1"
    number = "first"
    base_url = "https://{}dca.flcourts.gov/"
    search_url = "https://{}dca.flcourts.gov/search/opinions/?{}"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.court_id = self.__module__
        self.offset = 0
        self.from_date = None
        self.till_date = None

    def update_url(self) -> None:
        """Scrape last 7 days of opinions

        :return: none
        """
        # today = datetime.now().strftime("%m/%d/%Y")
        # prev = (datetime.now() - timedelta(days=7)).strftime("%m/%d/%Y")
        today = self.till_date.strftime("%m/%d/%Y")
        prev = self.from_date.strftime("%m/%d/%Y")

        params = {
            "offset": self.offset,
            "view": "embed",
            "startDate": prev,
            "endDate": today,
            "searchType": "opinions",
            "scopes[0]": f"{self.number}_district_court_of_appeal",
            "date[day]": "",
            "date[month]": "",
            "date[year]": "",
            "limit": "100",
            "sort": "opinion/disposition_date desc, opinion/case_number asc",
            "recentOnly": "0",
            "types[0]": "Written",
            "types[1]": "PCA",
            "types[2]": "Citation",
            "activeOnly": "0",
            "active_only": "0",
            "nonActiveOnly": "0",
            "nonactive_only": "0",
            "show_scopes": "0",
            "hide_search": "0",
            "hide_filters": "0",
            "siteaccess": f"{self.court_index}dca",
            "type[0]": "Written",
            "type[1]": "PCA",
            "type[2]": "Citation"
		}
        # old_params = {
        #     "sort": "opinion/disposition_date desc, opinion/case_number asc",
        #     "view": "full", "searchtype": "opinions", "limit": "10",
        #     "scopes[]": f"{self.number}_district_court_of_appeal",
        #     "type[]": ["pca", "written", ], "startdate": prev,
        #     "enddate": today, "date[year]": "", "date[month]": "",
        #     "date[day]": "", "query": "", "offset": self.offset, }
        self.url = self.search_url.format(self.court_index, urlencode(params))

    def _process_html(self) -> None:
        """Process the html and extract out the opinions
        Paginates if necessary

        :return: None
        """
        for row in self.html.xpath("//tr[.//td]"):
            if not row.xpath(".//a"):
                logger.debug("No document URL in row, skipping")
                continue

            # Row headers:
            # File, Type, Case No., Case Name, Disposition, Note, Release Date
            values = [
                cell.text_content().strip() for cell in row.xpath(".//td")
            ]

            # Prepend the district prefix as seen in the PDFs. If we don't do this
            # cases across districts will be merged
            docket_number = f"{self.court_index}D{values[2]}"

            url = row.xpath(".//a")[0].get("href")
            per_curiam = "per curiam" in values[4].lower()
            disposition = values[5].split("-")[0]

            self.cases.append(
                {
                    "name": titlecase(values[3]),
                    "date": values[6],
                    "disposition": disposition,
                    "url": urljoin(
                        self.base_url.format(self.court_index), url
                    ),
                    "status": "Published",
                    "docket": [docket_number],
                    "per_curiam": per_curiam,
                }
            )

        paginator_exists = self.html.xpath("//ul[@class='pagination']")
        paginator_disabled = self.html.xpath('//li[@class="next disabled"]')
        if (
            paginator_exists
            and not paginator_disabled
            and not self.test_mode_enabled()
        ):
            self.offset = self.offset + 100
            self.update_url()
            self.html = super()._download()
            self._process_html()

    def crawling_range(self, start_date: datetime, end_date: datetime) -> int:
        self.from_date = start_date
        self.till_date = end_date
        self.update_url()
        self.parse()
        return 0

    def get_class_name(self):
        return "fladistctapp_1"

    def get_court_name(self):
        return "District Courts of Appeal"

    def get_court_type(self):
        return "state"

    def get_state_name(self):
        return "Florida"





