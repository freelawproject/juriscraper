# Scraper for Minnesota Supreme Court
# CourtID: minn
# Court Short Name: MN
# Author: Andrei Chelaru
# Reviewer: mlr
# Date: 2014-07-03
# Contact:  Liz Reppe (Liz.Reppe@courts.state.mn.us), Jay Achenbach (jay.achenbach@state.mn.us)
import re
from datetime import date

from juriscraper.lib.string_utils import convert_date_string
from juriscraper.OpinionSite import OpinionSite


class Site(OpinionSite):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.court_id = self.__module__
        # Get 500 most recent results for the year.  This number could be reduced after the
        # initial run of this fixed code.  We need ot start with a big number though to
        # capture the cases we've missed over the past few weeks.
        self.url = "http://mn.gov/law-library-stat/search/opinions/?v:state=root%7Croot-0-500&query=date:{year}".format(
            year=date.today().year
        )
        self.court_filters = ["/supct/"]
        self.cases = []

    def _download(self, request_dict={}):
        html = super()._download(request_dict)
        self._extract_case_data_from_html(html)
        return html

    def _extract_case_data_from_html(self, html):
        """Build list of data dictionaries, one dictionary per case.

        Sometimes the XML is malformed, usually because of a missing docket number,
        which throws the traditional data list matching off.  Its easier and cleaner
        to extract all the data at once, and simply skip over records that do not
        present a docket number.
        """
        for document in html.xpath("//document"):
            docket = document.xpath('content[@name="docket"]/text()')
            if docket:
                docket = docket[0]
                title = document.xpath('content[@name="dc.title"]/text()')[0]
                name = self._parse_name_from_title(title)
                url = document.xpath("@url")[0]
                if any(s in url for s in self.court_filters):
                    # Only append cases that are in the right jurisdiction.
                    self.cases.append(
                        {
                            "name": name,
                            "url": self._file_path_to_url(
                                document.xpath("@url")[0]
                            ),
                            "date": convert_date_string(
                                document.xpath('content[@name="date"]/text()')[
                                    0
                                ]
                            ),
                            "status": self._parse_status_from_title(title),
                            "docket": docket,
                        }
                    )

    def _get_case_names(self):
        return [case["name"] for case in self.cases]

    def _get_download_urls(self):
        return [case["url"] for case in self.cases]

    def _file_path_to_url(self, path):
        return path.replace(
            "file:///web/prod/static/lawlib/live",
            "http://mn.gov/law-library-stat",
        )

    def _get_case_dates(self):
        return [case["date"] for case in self.cases]

    def _get_precedential_statuses(self):
        return [case["status"] for case in self.cases]

    def _parse_name_from_title(self, title):
        name_regex = re.compile(
            r"(?P<name>.+)\s(?:A(?:DM)?\d\d-\d{1,4})", re.I
        )
        return name_regex.search(title).group("name")

    def _parse_status_from_title(self, title):
        return "Unpublished" if "unpublished" in title.lower() else "Published"

    def _get_docket_numbers(self):
        return [case["docket"] for case in self.cases]
