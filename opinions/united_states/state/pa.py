# Scraper for the United States Court of Appeals for the Seventh Circuit
# CourtID: ca7
# Court Short Name: 7th Cir.

from juriscraper.OpinionSite import OpinionSite

class Site(OpinionSite):
    def __init__(self):
        self.url = 'http://www.pacourts.us/courts/supreme-court/court-opinions/'
        super(Site, self).__init__()
        self.court_id = self.__module__

    def _get_case_names(self):
        case_names = []
        for t in self.html.xpath('//*[@id="block_977"]/div[3]//strong/text()'):
            case_names.append(t)
        return case_names
"""
    def _get_download_urls(self):
        return [e for e in self.html.xpath('//table[2]/tr/td/table/tr[position() >=3]/td/a/@href')]

    def _get_case_dates(self):
        return [date.fromtimestamp(time.mktime(time.strptime(date_string.strip(), '%m/%d/%Y')))
                    for date_string in self.html.xpath('//table//table/tr[position() >= 3]/td[4]/text()')]

    def _get_docket_numbers(self):
        return [docket_number for docket_number in
                    self.html.xpath('//table//table/tr[position() >= 3]/td[1]/text()')]

    def _get_precedential_statuses(self):
        statuses = []
        for e in self.html.xpath('//table//table/tr[position() >= 3]/td[5]/a'):
            s = html.tostring(e, method='text', encoding='unicode').strip()
            if 'Opinion' in s:
                statuses.append('Published')
            elif 'Nonprecedential' in s:
                statuses.append('Unpublished')
            else:
                statuses.append('Unknown')
        return statuses

    def _get_nature_of_suit(self):
        natures = []
        for e in self.html.xpath('//table//table/tr[position() >= 3]/td[3]'):
            s = html.tostring(e, method='text', encoding='unicode')
            natures.append(s)
        return natures
"""
