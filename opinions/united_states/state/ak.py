from GenericSite import GenericSite
import time
from datetime import date

class Site(GenericSite):
    def __init__(self):
        super(Site, self).__init__()
        self.url = 'http://www.appellate.courts.state.ak.us/list.asp'
        self.method = 'POST'
        self.parameters = {
            'R1' : 'A',
            'R2' : 'Null',
            'D1' : 'None',
            'B1' : 'Submit',
        }
        self.court_id = self.__module__

    def _get_case_names(self):
        return [e for e in self.html.xpath('/html/body/div[position()>1]//table//tr[position() > 1]/td[1]//text()')]

    def _get_download_links(self):
        download_links = []
        for e in self.html.xpath('/html/body/div[position()>1]//table//tr[position() > 1]/td[2]/a/@href'):
            download_links.append(e)
        return download_links

    def _get_case_dates(self):
        dates = []
        for date_string in self.html.xpath('/html/body/div[position()>1]//table//tr[position() > 1]/td[3]/text()'):
            val = date_string.strip()
            if val == '':
                dates.append('')
            else:
                dates.append(date.fromtimestamp(time.mktime(time.strptime(val, '%m/%d/%y'))))
        return dates

    def _get_docket_numbers(self):
        docket_numbers = []
        for date_string in self.html.xpath('/html/body/div[position()>1]//table//tr[position() > 1]/td[3]/text()'):
            docket_numbers.append("")
        return docket_numbers
        
    def _get_precedential_statuses(self):
        precedential_statuses = []
        for date_string in self.html.xpath('/html/body/div[position()>1]//table//tr[position() > 1]/td[3]/text()'):
            precedential_statuses.append("Published")
        return precedential_statuses