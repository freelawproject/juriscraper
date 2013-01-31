# Scraper for the United States Court of Appeals for Veterans Claims
# CourtID: cavc
# Court Short Name: Vet.App.
from juriscraper.opinions.united_states.federal_special import cavc
from lxml import html

class Site(cavc.Site):
    def __init__(self):
        super(Site, self).__init__()
        self.url = 'http://www.uscourts.cavc.gov/orders_and_opinions/Opinions20042ndQuarter.cfm'
        self.court_id = self.__module__

    def _get_case_names(self):
        case_names = []
        for txt in (self.html.xpath(
                '//table[1]/tbody/tr/td[3]/p/text()')):
            if txt == 'Rule 26(b)':
                case_names.append('In Re: A Proposed Amendment to Rule 26(b)')
            else:
                case_names.append(txt + ' v. Principi')
        return case_names