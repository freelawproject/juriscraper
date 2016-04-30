# Scraper for Minnesota Supreme Court
#CourtID: minn
#Court Short Name: MN
#Author: Andrei Chelaru
#Reviewer: mlr
#Date: 2014-07-03

from juriscraper.OpinionSite import OpinionSite
from juriscraper.lib.string_utils import convert_date_string


class Site(OpinionSite):
    court_abbreviation = 'supct'

    def __init__(self, *args, **kwargs):
        super(Site, self).__init__(*args, **kwargs)
        self.court_id = self.__module__
        self.url = 'http://mn.gov/law-library/search/index.jsp?v%3Asources=mn-law-library-opinions&query=+%28url%3A%2Farchive%2F' + \
                   self.court_abbreviation + '%29+&sortby=date'

    def _get_case_names(self):
        return [name.strip() for name in self.html.xpath("//a[@class='searchresult_title']/text()")]

    def _get_download_urls(self):
        return [url.strip() for url in self.html.xpath("//span[@class='searchresult_url']/text()")]

    def _get_case_dates(self):
        dates = []
        for date in self.html.xpath("//div[@class='searchresult_date']/text()"):
            date = date.strip()
            if date:
                date = ' '.join(date.strip().split())
                dates.append(convert_date_string(date))
        return dates

    def _get_precedential_statuses(self):
        return ['Published'] * len(self.case_names)

    def _get_docket_numbers(self):
        """At the time of coding, the only reliable way to get docket numbers
        is from the resource url.  Sometimes they are included in the case names
        but many cases are too long, cut off, and do not include them.  We also
        have to guess at their standard numbering convention, assuming A##-####,
        which is the correct format the majority of the time, but sometimes they
        seem to drop a zero in the case of A##-0###.
        """
        dockets = []
        for url in self._get_download_urls():
            file_name = url.split('/')[-1]
            docket = file_name.split('-')[0].upper()[2:]
            dockets.append('%s-%s' % (docket[:3], docket[3:]))
        return dockets

    def _get_summaries(self):
        return [summary.strip() for summary in self.html.xpath("//div[@class='searchresult_snippet']/text()")]
