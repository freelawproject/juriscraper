from juriscraper.OpinionSite import OpinionSite
from juriscraper.lib.string_utils import clean_string
import time
from datetime import date
from lxml import html


class Site(OpinionSite):
    def __init__(self, *args, **kwargs):
        super(Site, self).__init__(*args, **kwargs)
        self.url = 'http://www.courtswv.gov/supreme-court/opinions.html'
        self.court_id = self.__module__

    def _get_case_names(self):
        return [t for t in self.html.xpath('//table/tbody/tr/td[3]/a[1]/text()')]

    def _get_download_urls(self):
        return [href for href in
                self.html.xpath('//table/tbody/tr/td[3]/a[1]/@href')]

    def _get_case_dates(self):
        dates = []
        for date_string in self.html.xpath('//table/tbody/tr/td[1]/text()'):
            dates.append(date.fromtimestamp(time.mktime(time.strptime(clean_string(date_string), '%m/%d/%Y'))))
        return dates

    def _get_docket_numbers(self):
        nums = []
        for e in self.html.xpath('//table/tbody/tr/td[2]'):
            nums.append(html.tostring(e, method='text', encoding='unicode').lower().strip())
        return nums

    def _get_precedential_statuses(self):
        statuses = []
        for status in self.html.xpath('//table/tbody/tr/td[5]/text()'):
            if status.lower() == 'md':
                statuses.append('Published')
            elif status.lower() == 'so':
                statuses.append('Published')
            elif status.lower() == 'pc':
                statuses.append('Published')
            elif status.lower() == 'sep':
                statuses.append('Separate')
            else:
                statuses.append('Unknown')
        return statuses

    def _get_nature_of_suit(self):
        natures = []
        for t in self.html.xpath('//table/tbody/tr/td[4]/text()'):
            # List is sourced from JS in scraped HTML
            if t == "CR-F":
                natures.append('Felony (non-Death Penalty)')
            elif t == "CR-M":
                natures.append('Misdemeanor')
            elif t == "CR-O":
                natures.append('Criminal-Other')
            elif t == "TCR":
                natures.append('Tort, Contract, and Real Property')
            elif t == "PR":
                natures.append('Probate')
            elif t == "FAM":
                natures.append('Family')
            elif t == "JUV":
                natures.append('Juvenile')
            elif t == "CIV-O":
                natures.append('Civil-Other')
            elif t == "WC":
                natures.append('Workers Compensation')
            elif t == "TAX":
                natures.append('Revenue (Tax)')
            elif t == "ADM":
                natures.append('Administrative Agency-Other')
            elif t == "MISC":
                natures.append('Appeal by Right-Other')
            elif t == "OJ-H":
                natures.append('Habeas Corpus')
            elif t == "OJ-M":
                natures.append('Writ Application-Other')
            elif t == "OJ-P":
                natures.append('Writ Application-Other')
            elif t == "L-ADM":
                natures.append('Bar Admission')
            elif t == "L-DISC":
                natures.append('Bar Discipline/Eligibility')
            elif t == "L-DISC-O":
                natures.append('Bar/Judiciary Proceeding-Other')
            elif t == "J-DISC":
                natures.append('Bar/Judiciary Proceeding-Other')
            elif t == "CERQ":
                natures.append('Certified Question')
            elif t == "OJ-O":
                natures.append('Original Proceeding/Appellate Matter-Other')
            else:
                natures.append('Unknown')
        return natures
