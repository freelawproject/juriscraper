#Scraper for New Hampshire Supreme Court
#CourtID: nh
#Court Short Name: NH
#Author: Andrei Chelaru
#Reviewer: mlr
#History:
# - 2014-06-27: Created
# - 2014-10-17: Updated by mlr to fix regex error.
# - 2015-06-04: Updated by bwc so regex catches comma, period, or whitespaces
#   as separator. Simplified by mlr to make regexes more semantic.
# - 2016-02-20: Updated by arderyp to handle strange format where multiple
#   case names and docket numbers appear in anchor text for a single case
#   pdf link. Multiple case names are concatenated, and docket numbers are
#   concatenated with ',' delimiter

import re
from datetime import date

from juriscraper.OpinionSite import OpinionSite
from juriscraper.lib.string_utils import convert_date_string


class Site(OpinionSite):
    def __init__(self, *args, **kwargs):
        super(Site, self).__init__(*args, **kwargs)
        self.url = 'http://www.courts.state.nh.us/supreme/opinions/{current_year}/index.htm'.format(
            current_year=date.today().year)
        self.court_id = self.__module__
        self.link_path = 'id("content")/div//ul//li//a[position()=1]'
        self.link_text_regex = re.compile('(\d{4}-\d+(?!.*\d{4}-\d+))(?:,|\.|\s?) (.*)')

    def _get_case_names(self):
        case_names = []
        for link in self.html.xpath(self.link_path):
            # Text of some links includes info for multiple cases split by <br>
            # so we'll iterate over each, extract the name, clean it up, then
            # glue the names together to form one long name. (Example: Feb2016)
            link_names = []
            for text in link.xpath('text()'):
                name_raw = self.link_text_regex.search(text).group(2)
                if name_raw:
                    link_names.append(' '.join(name_raw.split()))
            case_names.append(' and '.join(link_names))
        return case_names

    def _get_download_urls(self):
        path = "id('content')/div//ul//li//a[position()=1]"
        download_url = []
        for element in self.html.xpath(path):
            url = element.xpath('./@href')[0]
            download_url.extend([url])
        return download_url

    def _get_case_dates(self):
        dates = []
        path = 'id("content")/div//strong'
        sub_path = './following-sibling::ul[1]//li|../following-sibling::ul[1]//li'
        for element in self.html.xpath(path):
            text = element.text_content().strip(':')
            try:
                case_date = convert_date_string(text)
            except ValueError:
                # Sometimes the court includes "To be released..."
                # sections, without links, which we skip here
                continue
            dates.extend([case_date] * len(element.xpath(sub_path)))
        return dates

    def _get_precedential_statuses(self):
        return ['Published'] * len(self.case_names)

    def _get_docket_numbers(self):
        docket_numbers = []
        for link in self.html.xpath(self.link_path):
            # Text of some links includes info for multiple cases split by <br> so we'll
            # iterate over each, extract the docket number, then glue the numbers together
            # to create a single "xx,yy" docket number. (Example: Feb2016)
            case_dockets = []
            for text in link.xpath('text()'):
                docket = self.link_text_regex.search(text).group(1)
                if docket:
                    case_dockets.append(docket)
            docket_numbers.append(', '.join(case_dockets))
        return docket_numbers
