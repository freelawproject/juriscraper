"""Scraper for the United States Court of Appeals for Veterans Claims
CourtID: cavc
Court Short Name: Vet. App.
History:
 - 2012-06-07: Created by Brian Carver
 - 2014-08-06: Updated by mlr.
 - 2023-01-23: Update by William Palin
"""

import datetime
from datetime import date
from typing import Optional

from juriscraper.DeferringList import DeferringList
from juriscraper.OpinionSiteLinear import OpinionSiteLinear


class Site(OpinionSiteLinear):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.url = "http://www.uscourts.cavc.gov/opinions.php"
        self.court_id = self.__module__
        self.base = (
            "https://efiling.uscourts.cavc.gov/cmecf/servlet/TransportRoom"
        )
        self.seeds = []
        self.last_month = date.today() - datetime.timedelta(days=31)
        self.status = "Published"

    def _process_html(self):
        """Process the CAVC website and collect new opinions

        :return: None
        """
        cases = self.html.xpath(".//tbody/tr/td/a/parent::td/parent::tr")
        for case in cases:
            try:
                name, date = case.xpath(".//td/text()")
                docket = case.xpath(".//a/text()")[0]
                document_url = case.xpath(".//a/@href")[0]
                clean_date = datetime.datetime.strptime(date, "%d%b%y")
                if self.last_month > clean_date.date():
                    break
                clean_date_string = clean_date.strftime("%m/%d/%Y")
                url = f"{self.base}?servlet=CaseSummary.jsp&caseNum={docket}&incOrigDkt=Y&incDktEntries=Y"
                self.seeds.append(url)
                self.cases.append(
                    {
                        "url": document_url,
                        "date": clean_date_string,
                        "docket": docket,
                    }
                )
            except ValueError:
                # An opinion was malformed. I'd rather skip it for now
                continue

    def _get_case_names(self) -> DeferringList:
        """Get case names using a deferring list."""

        def get_name(url) -> Optional[str]:
            # """Abstract out the case name from the case page."""
            if self.test_mode_enabled():
                return "No case names fetched during tests."
            self.url = url
            self.html = self._download()
            case_name = self.html.xpath('.//tr[contains(., " v. ")]')[
                -1
            ].text_content()
            return case_name

        return DeferringList(seed=self.seeds, fetcher=get_name)
