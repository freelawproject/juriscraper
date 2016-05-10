# Scraper for Oklahoma Attorney General Opinions
#CourtID: oklaag
#Court Short Name: OK
#Author: Andrei Chelaru
#Reviewer: mlr
#Date: 2014-07-05

from datetime import date

from juriscraper.opinions.united_states.state import okla
from lxml import html


class Site(okla.Site):
    def __init__(self, *args, **kwargs):
        super(Site, self).__init__(*args, **kwargs)
        d = date.today()
        self.url = 'http://www.oscn.net/applications/oscn/Index.asp?ftdb=STOKAG&year={year}&level=1'.format(
            year=d.year
        )
        self.court_id = self.__module__

    def _get_precedential_statuses(self):
        return ['Unpublished'] * len(self.case_names)

    @staticmethod
    def cleanup_content(content):
        tree = html.fromstring(content)
        core_element = tree.xpath('//div[contains(concat(" ", normalize-space(@class), " "), " main ")]')[0]
        return html.tostring(
            core_element,
            pretty_print=True,
            encoding='unicode'
        )

