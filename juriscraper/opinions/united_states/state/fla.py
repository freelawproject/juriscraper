# Scraper for Florida Supreme Court
# CourtID: fla
# Court Short Name: fla

from datetime import date, datetime, timedelta
from typing import Optional
from urllib.parse import urljoin

from juriscraper.AbstractSite import logger
from juriscraper.lib.string_utils import titlecase
from juriscraper.OpinionSiteLinear import OpinionSiteLinear


class Site(OpinionSiteLinear):
    # make a backscrape request every `days_interval` range, to avoid pagination
    days_interval = 20
    first_opinion_date = datetime(1999, 9, 23)
    # even though you can put whatever number you want as limit, 50 seems to be
    # the max
    base_url = "https://flcourts-media.flcourts.gov/_search/opinions/?limit=50&offset=0&query=&scopes[]={}&searchtype=opinions&siteaccess={}&startdate={}&enddate={}"
    scopes = "supreme_court"
    site_access = "supreme2"
    # Example built URL
    # "https://flcourts-media.flcourts.gov/_search/opinions/?startdate=2025-07-01&limit=50&offset=0&query=&scopes[]=supreme_court&searchtype=opinions&siteaccess=supreme2&enddate=2026-01-01"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.court_id = self.__module__
        self.status = "Published"
        self.set_url()
        self.make_backscrape_iterable(kwargs)

    def _process_html(self) -> None:
        """Parses HTML into case dictionaries

        :return: None
        """
        json = self.html
        for row in json["searchResults"]:
            fields = row["content"]["fields"]
            if (fields.get("note", "") or "") in ("Notice of Correction",):
                logger.info("Skipping non-opinion document %s", fields)
                continue

            name = fields.get("case_style", "")
            if not name:
                # These seem to be family - children related cases. See example
                # in district 4 example file
                # https://flcourts-media.ccplatform.net/content/download/2472477/28965542?version=5
                logger.info("Skipping case with no name %s", fields)
                continue

            disposition = fields.get("disposition", "") or ""
            self.cases.append(
                {
                    "url": urljoin(self.base_url, fields["opinion"]["uri"]),
                    "docket": self.get_docket_number(fields["case_number"]),
                    "name": titlecase(name),
                    "date": fields["disposition_date"]["date"]["date"].split(
                        " "
                    )[0],
                    "disposition": self.get_disposition(
                        disposition, fields.get("note", "")
                    ),
                    "status": self.status,
                    "per_curiam": "per curiam" in disposition.lower(),
                }
            )

    def get_docket_number(self, raw_docket_number: str) -> str:
        """Prepend the district code to a docket number

        This is useful to disambiguate district court of appeals docket numbers

        :param raw_docket_number: the docket number as returned by the source
        :return: the clean docket number
        """
        return raw_docket_number

    def get_disposition(self, raw_disposition: str, note: str) -> str:
        """Get a valid disposition value from raw values

        :param raw_disposition: the raw disposition in the returned json
        :param note: a value in the return json that may contain a disposition
        return: A clean disposition value
        """
        return titlecase(raw_disposition)

    def set_url(
        self, start: Optional[date] = None, end: Optional[date] = None
    ) -> None:
        """Sets URL using date arguments

        If not dates are passed, get 50 most recent opinions

        :param start: start date
        :param end: end date
        :return: none
        """
        if not start:
            end = datetime.today()
            start = end - timedelta(days=365)

        fmt = "%Y-%m-%d"
        self.url = self.base_url.format(
            self.scopes,
            self.site_access,
            start.strftime(fmt),
            end.strftime(fmt),
        )

    def _download_backwards(self, dates: tuple[date, date]) -> None:
        """Overrides scraper URL using date inputs

        :param dates: (start_date, end_date) tuple
        :return None
        """
        self.set_url(*dates)
        logger.info("Backscraping for range %s %s", *dates)
