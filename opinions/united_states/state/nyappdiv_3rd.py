# Scraper for New York Appellate Divisions 3rd Dept.
# CourtID: nyappdiv_3rd
# Court Short Name: NY
# History:
#   2014-07-04: Created by Andrei Chelaru
#   2014-07-05: Reviewed by mlr
#   2014-12-15: Updated to fix regex and insanity errors.
#   2016-02-17: Updated by arderyp, regex was breaking due to new page section.
#   2016-03-08: Updated by arderyp, Added regex back to handle human typos found
#               on older pages, and added fallback loose checking to handle
#               differently formatted disciplinary/admissions docket numbers

import re

from datetime import date
from dateutil.relativedelta import relativedelta, TH
from juriscraper.OpinionSite import OpinionSite


class Site(OpinionSite):
    def __init__(self, *args, **kwargs):
        super(Site, self).__init__(*args, **kwargs)
        self.court_id = self.__module__
        # Last thursday, this court publishes weekly
        self.crawl_date = date.today() + relativedelta(weekday=TH(-1))
        self.url = 'http://decisions.courts.state.ny.us/ad3/CalendarPages/nc{month_nr}{day_nr}{year}.htm'.format(
            month_nr=self.crawl_date.strftime("%m"),
            day_nr=self.crawl_date.strftime("%d"),
            year=self.crawl_date.year
        )
        self.LINK_PATH = "//td[2]//a[contains(./@href, 'Decisions')]"
        self.LINK_TEXT_PATH = '%s/text()' % self.LINK_PATH
        self.LINK_HREF_PATH = '%s/@href' % self.LINK_PATH
        self.LINK_TEXT_PATTERN = r'^(\d+(/\d+)?)(/)?(.+)'

    def _get_case_names(self):
        case_names = []
        for link_text in self.html.xpath(self.LINK_TEXT_PATH):
            docket, name = self._get_docket_and_name_from_text(link_text)
            if name:
                case_names.append(name)
        return case_names

    def _get_download_urls(self):
        return list(self.html.xpath(self.LINK_HREF_PATH))

    def _get_case_dates(self):
        return [self.crawl_date] * len(self.html.xpath(self.LINK_HREF_PATH))

    def _get_precedential_statuses(self):
        return ['Published'] * len(self.case_names)

    def _get_docket_numbers(self):
        docket_numbers = []
        for link_text in self.html.xpath(self.LINK_TEXT_PATH):
            docket, name = self._get_docket_and_name_from_text(link_text)
            if docket:
                docket_numbers.append(docket)
        return docket_numbers

    def _get_docket_and_name_from_text(self, text):
        """Parse docket number and name from link text

        There are multiple docket number formats, and there are also
        instances of human typos that were breaking "logical" approaches
        to parsing this data.  This is a loose approach that will fall
        back on accepting the first space delimited element as the docket,
        and will handle instances of human typos we've seen where a clerk
        entered "######/Case name" instead of "###### Case name" or
        "######/###### Case name".
        """

        text = text.strip()
        if not text:
            return False, False
        data = re.search(self.LINK_TEXT_PATTERN, text)
        if data and data.group(1) and data.group(4):
            # Docket is a standard xxxxxx or xxxxxx/yyyyyy number
            docket = data.group(1)
            name = ' '.join(data.group(4).split())
        else:
            # For most flexibility, assume docket is first substring in text
            parts = text.split(None, 1)
            docket = parts[0]
            name = parts[1]
        return docket, name




