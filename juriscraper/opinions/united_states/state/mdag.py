"""Scraper for the Maryland Attorney General
CourtID: ag
Court Short Name: Maryland Attorney General
"""

from lxml import html
import datetime
from juriscraper.OpinionSite import OpinionSite
from juriscraper.lib.string_utils import convert_date_stringq


class Site(OpinionSite):
    """This scraper is strange. The site it temperamental, and the javascript
    seems to load successfully on some runs, but not on others. The dates are
    also estimated, and the names are actually semi-long summaries. Furthermore,
    the site's source is unmanageable, which has prevented us from being able to
    create legitimate test/example files for coverage. We have a single example
    file that's an empty document skeleton to prevent the test mechanism from
    complaining. But it isn't a test providing real coverage.

    We are doing the best we can with a bad site.

    Note: While this site use ASPX, it is not an OpinionSiteASPX because it
    simply downloads JSON from an endpoint and doesn't use any of the features
    of that class.
    """

    def __init__(self, *args, **kwargs):
        super(Site, self).__init__(*args, **kwargs)
        self.court_id = self.__module__
        self.year = datetime.date.today().year
        self.url = (
            "http://www.marylandattorneygeneral.gov/_layouts/15/inplview.aspx"
        )
        self.back_scrape_iterable = range(1993, self.year + 1)

    def _download(self, request_dict={}):
        params = {
            "List": "{1BA692B1-E50C-4754-AADD-E6753F46B403}",
            "IsXslView": "TRUE",
            "IsCSR": "TRUE",
            "ListViewPageUrl": "http://www.marylandattorneygeneral.gov/Pages/Opinions/index.aspx",
            "GroupString": ";#%s;#" % self.year,
            "IsGroupRender": "TRUE",
            "WebPartID": "{E1A60D10-12C0-4029-8BE0-BA5F9AC93BF8}",
        }

        r = self.request["session"].post(self.url, params=params)
        self.json = r.json()
        return html.fromstring(r.text)

    def _get_case_names(self):
        return [x["Summary"] for x in self.json["Row"]]

    def _get_download_urls(self):
        return [x["FileRef.urlencodeasurl"] for x in self.json["Row"]]

    def _get_case_dates(self):
        today = datetime.date.today()
        count = len(self._get_case_names())
        middle_of_year = convert_date_string("July 2, %d" % self.year)
        if self.year == today.year:
            # Not a backscraper, assume cases were filed on day scraped.
            return [today] * count
        else:
            # All we have is the year, so estimate the middle most day
            return [middle_of_year] * count

    def _get_docket_numbers(self):
        return [x["Title"] for x in self.json["Row"]]

    def _get_precedential_statuses(self):
        return [
            "Published" if "unpublished" not in x["Title"] else "Unpublished"
            for x in self.json["Row"]
        ]

    def _get_date_filed_is_approximate(self):
        return ["True"] * len(self.case_names)

    def _download_backwards(self, year):
        self.year = year
        self.html = self._download()
