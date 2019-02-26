"""
History:
 - 2014-08-05: Adapted scraper to have year-based URLs.
"""

from juriscraper.OpinionSite import OpinionSite
from juriscraper.lib.string_utils import convert_date_string


class Site(OpinionSite):
    def __init__(self, *args, **kwargs):
        super(Site, self).__init__(*args, **kwargs)
        self.court_id = self.__module__
        self.url = 'https://www.courts.oregon.gov/publications/sc/Pages/default.aspx'
        self.cases = []

    def _download(self, request_dict={}):
        html = super(Site, self)._download(request_dict=request_dict)
        self.extract_cases(html)

    def extract_cases(self, html):
        for header in html.xpath('//h4//a/parent::h4'):
            date_string = header.text_content().strip()
            if not date_string:
                continue
            date = convert_date_string(date_string)
            ul = header.xpath('./following-sibling::ul')[0]
            for item in ul.xpath('.//li'):
                text = item.text_content().strip()
                url = item.xpath('.//a[1]/@href')[0]
                docket = item.xpath('.//a[2]')[0].text_content().strip()
                name = text.split(')', 1)[-1]
                self.cases.append({
                    'date': date,
                    'name': name,
                    'docket': docket,
                    'url': url,
                })

    def _get_case_names(self):
        return [case['name'] for case in self.cases]

    def _get_docket_numbers(self):
        return [case['docket'] for case in self.cases]

    def _get_download_urls(self):
        return [case['url'] for case in self.cases]

    def _get_case_dates(self):
        return [case['date'] for case in self.cases]

    def _get_precedential_statuses(self):
        return ["Published"] * len(self.cases)
