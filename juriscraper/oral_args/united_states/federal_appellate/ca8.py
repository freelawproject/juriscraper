"""Oral Argument Audio Scraper for Eighth Circuit Court of Appeals
CourtID: ca8
Court Short Name: 8th Cir.
Author: Brian W. Carver
Date created: 2014-06-21
History:
 - 2014-07-22: download_url fixed by mlr
"""

from datetime import datetime

from juriscraper.OralArgumentSite import OralArgumentSite
from juriscraper.lib.string_utils import clean_if_py3


class Site(OralArgumentSite):
    def __init__(self, *args, **kwargs):
        super(Site, self).__init__(*args, **kwargs)
        self.court_id = self.__module__
        self.url = "http://media-oa.ca8.uscourts.gov/circ8rss.xml"

    def _download(self, request_dict={}):
        """Go through the items and filter out ones that aren't complete."""
        self.items = []
        html_tree = super(Site, self)._download(request_dict=request_dict)
        for item in html_tree.xpath("//item"):
            case_name = item.xpath("./title/text()")[0].split(":", 1)[1]
            if case_name.strip():
                self.items.append(item)

        # Set self.html to None so it can't be misused.
        return None

    def _get_download_urls(self):
        return [item.xpath("./enclosure/@url")[0] for item in self.items]

    def _get_case_names(self):
        case_names = []
        for txt in [item.xpath("./title/text()")[0] for item in self.items]:
            case_name = clean_if_py3(txt).split(": ", 1)[1]
            case_names.append(case_name)
        return case_names

    def _get_case_dates(self):
        case_dates = []
        for txt in [
            item.xpath("./description/text()")[0] for item in self.items
        ]:
            # I can't see it, but there's apparently whitespace or a newline
            # at the end of these dates that has to be removed or we error out.
            case_date = clean_if_py3(txt).split("about ", 1)[1].strip()
            case_dates.append(datetime.strptime(case_date, "%m/%d/%Y").date())
        return case_dates

    def _get_docket_numbers(self):
        docket_numbers = []
        for txt in [item.xpath("./title/text()")[0] for item in self.items]:
            docket_number = clean_if_py3(txt).split(": ", 1)[0]
            docket_numbers.append(docket_number)
        return docket_numbers
