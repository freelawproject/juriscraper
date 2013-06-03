from juriscraper.GenericSite import GenericSite
import time
from datetime import date

class Site(GenericSite):
    def __init__(self):
        super(Site, self).__init__()
        self.url = 'http://www.ca5.uscourts.gov/Opinions.aspx?View=Last7'
        self.court_id = self.__module__


    def _get_case_names(self):
        return [e for e in self.html.xpath('//table[@id = "tblPublished" or @id = "tblUnpublished"]//tr[position() > 1]/td[3]//text()')]

    def _get_download_urls(self):
        return [e for e in self.html.xpath('//table[@id = "tblPublished" or @id = "tblUnpublished"]//tr[position() > 1]/td[1]//a/@href')]

    def _get_case_dates(self):
        dates = []
        for date_string in self.html.xpath('//table[@id = "tblPublished" or @id = "tblUnpublished"]//tr[position() > 1]/td[2]//text()'):
            dates.append(date.fromtimestamp(time.mktime(time.strptime(date_string, '%m/%d/%Y'))))
        return dates

    def _get_docket_numbers(self):
        return [e for e in self.html.xpath('//table[@id = "tblPublished" or @id = "tblUnpublished"]//tr[position() > 1]/td[1]//a/text()')]

    def _get_precedential_statuses(self):
        statuses = []
        for link in self.download_urls:
            if "unpub" in link:
                statuses.append("Unpublished")
            elif "pub" in link:
                statuses.append("Published")
            else:
                statuses.append("Unknown")
        return statuses
