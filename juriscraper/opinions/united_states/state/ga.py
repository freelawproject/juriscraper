#  Scraper for Georgia Supreme Court
# CourtID: ga
# Court Short Name: ga
# History:
#  - 2014-07-25: Created by Andrei Chelaru, reviewed by mlr
#  - 2015-07-30: MLR: Added more lenient dates.
#  - 2016-09-02: arderyp: fixed to handle slight site redesign, while accomodating legacy

import re
from datetime import date

from juriscraper.OpinionSite import OpinionSite
from juriscraper.lib.string_utils import titlecase
from juriscraper.lib.string_utils import convert_date_string


class Site(OpinionSite):
    def __init__(self, *args, **kwargs):
        super(Site, self).__init__(*args, **kwargs)
        self.court_id = self.__module__
        self.url = 'http://www.gasupreme.us/opinions/{year}-opinions/'.format(year=date.today().year)
        self.cases = []

    def _download(self, request_dict={}):
        html = super(Site, self)._download(request_dict)
        self.extract_cases_from_html(html)
        return html

    def extract_cases_from_html(self, html):
        paths = '//p/strong | //p/b | //p/font/strong | //p/font/b'
        for date_element in html.xpath(paths):
            string = date_element.xpath('./text()')
            try:
                string = string[0]
                # handle examples where time but no date (ga_example_3.html)
                if ':' in string and ('AM' in string or 'PM' in string):
                    continue
                # handle legacy example (ga_example.html)
                string = string.split('SUMMARIES')[0]
                date_string = re.sub(r'\W+', ' ', string)
                # handle legacy example (ga_example.html)
                if len(date_string.split()) != 3:
                    continue
                case_date = convert_date_string(date_string)
            except:
                continue
            parent = date_element.xpath('./..')[0]
            # handle legacy example (ga_example.html)
            while parent.tag != 'p':
                parent = parent.xpath('./..')[0]
            for item in parent.getnext().xpath('./li'):
                text = item.text_content()
                if text:
                    split = text.split('.', 1)
                    self.cases.append({
                        'date': case_date,
                        'url': item.xpath('//a[1]/@href')[0],
                        'docket': split[0].rstrip('.'),
                        'name': titlecase(split[1]),
                    })

    def _get_case_names(self):
        return [case['name'] for case in self.cases]

    def _get_download_urls(self):
        return [case['url'] for case in self.cases]

    def _get_case_dates(self):
        return [case['date'] for case in self.cases]

    def _get_docket_numbers(self):
        return [case['docket'] for case in self.cases]

    def _get_precedential_statuses(self):
        return ['Published'] * len(self.cases)
