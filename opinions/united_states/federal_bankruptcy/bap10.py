"""
Scraper for the United States Bankruptcy Appellate Panel for the Tenth Circuit
CourtID: bap10
Court Short Name: 10th Cir. BAP
Auth: Jon Andersen <janderse@gmail.com>
Reviewer:
History:
    2014-09-01 First draft by Jon Andersen
"""

from juriscraper.OpinionSite import OpinionSite
import time
from datetime import date
import lxml


class Site(OpinionSite):
    def __init__(self):
        super(Site, self).__init__()
        self.url = 'http://www.bap10.uscourts.gov/opinions/new/opinion.txt'
        self.court_id = self.__module__
        self.my_case_names = []
        self.my_download_urls = []
        self.my_docket_numbers = []

    def _get_case_dates(self):
        """
        Parse opinion.txt and ignores duplicates.  Lines like:
        13-94.pdf|13|94|08/25/2014|Steve Christensen|Raymond Madsen|United States Bankruptcy Court for the District of Utah
        """
        dates = []
        rows = lxml.html.tostring(self.html)
        alreadyseen = []
        for s in rows.splitlines():
            s = s.replace("<p>", "").replace("</p>", "").strip()
            if s in alreadyseen:
                continue
            if s == "":
                continue
            alreadyseen.append(s)
            (pdf, yr, num, casedate, p1, p2, court) = s.split("|")
            self.my_download_urls.append(
                'http://www.bap10.uscourts.gov/opinions/%s/%s' % (yr, pdf))
            self.my_case_names.append("%s v. %s" % (p1, p2))
            self.my_docket_numbers.append("%s-%s" % (yr, num))
            dates.append(
                date.fromtimestamp(
                    time.mktime(time.strptime(casedate, '%m/%d/%Y'))))
        return dates

    def _get_case_names(self):
        return self.my_case_names

    def _get_download_urls(self):
        return self.my_download_urls

    def _get_precedential_statuses(self):
        return ["Unknown"] * len(self.case_dates)

    def _get_docket_numbers(self):
        return self.my_docket_numbers
