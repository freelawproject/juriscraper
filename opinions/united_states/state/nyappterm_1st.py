# Scraper and Back Scraper for New York Appellate Term 1st Dept.
# CourtID: nyappterm_1st
# Court Short Name: NY
# Author: Andrei Chelaru
# Reviewer:
# Date: 2015-10-30
from datetime import date, timedelta

from juriscraper.opinions.united_states_backscrapers.state.ny import Site as NySite
from juriscraper.AbstractSite import logger
from juriscraper.lib.network_utils import add_delay


class Site(NySite):

    def __init__(self, *args, **kwargs):
        super(Site, self).__init__(*args, **kwargs)
        self.court = 'Appellate+Term,+1st+Dept'
        self.interval = 30

        self.parameters = {
            'rbOpinionMotion': 'opinion',
            'Pty': '',
            'and_or': 'and',
            'dtStartDate': (date.today() - timedelta(days=self.interval)).strftime("%m/%d/%Y"),
            'dtEndDate': date.today().strftime("%m/%d/%Y"),
            'court': self.court,
            'docket': '',
            'judge': '',
            'slipYear': '',
            'slipNo': '',
            'OffVol': '',
            'OffPage': '',
            'fullText': '',
            'and_or2': 'and',
            'Submit': 'Find',
            'hidden1': '',
            'hidden2': ''

        }

    def parse(self):
        if self.status is None:
            self.set_cookies()
            logger.info("Using cookies: %s" % self.cookies)
            self.html = self._download(request_dict={'cookies': self.cookies})
            # Run the downloader if it hasn't been run already

            i = 0
            while not self.html.xpath('//table') and i < 10:
                add_delay(20, 5)
                self.html = self._download(request_dict={'cookies': self.cookies})
                i += 1
                logger.info("Got a bad response {} time(s)".format(i))

        # Set the attribute to the return value from _get_foo()
        # e.g., this does self.case_names = _get_case_names()
        for attr in self._all_attrs:
            self.__setattr__(attr, getattr(self, '_get_%s' % attr)())

        self._clean_attributes()
        if 'case_name_shorts' in self._all_attrs:
            # This needs to be done *after* _clean_attributes() has been run.
            # The current architecture means this gets run twice. Once when we
            # iterate over _all_attrs, and again here. It's pretty cheap though.
            self.case_name_shorts = self._get_case_name_shorts()
        self._post_parse()
        self._check_sanity()
        self._date_sort()
        self._make_hash()
        return self