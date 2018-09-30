#Scraper for New Hampshire Supreme Court
#CourtID: nh
#Court Short Name: NH
#Court Contact: webmaster@courts.state.nh.us
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
from juriscraper.lib.exceptions import InsanityException
from juriscraper.lib.string_utils import convert_date_string


class Site(OpinionSite):
    def __init__(self, *args, **kwargs):
        super(Site, self).__init__(*args, **kwargs)
        self.url = 'http://www.courts.state.nh.us/supreme/opinions/{current_year}/index.htm'.format(
            current_year=date.today().year)
        self.court_id = self.__module__
        self.link_path = 'id("content")/div//ul//li//a[position()=1]'
        self.link_text_regex = re.compile('(\d{4}-\d+(?!.*\d{4}-\d+))(?:,|\.|\s?) (.*)')
        self.docket_name_pairs = False

    def _get_case_names(self):
        self.docket_name_pairs = self._get_anchor_docket_name_pairs()
        return [pair['name'] for pair in self.docket_name_pairs]

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
            text = element.text_content().strip().rstrip(':')
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
        return [pair['docket'] for pair in self.docket_name_pairs]

    def _get_anchor_docket_name_pairs(self):
        """The court has some ugly HTML practices that we need to handle.

        Most anchor links include single line strings with a single docket
        number and a single case name.  However, there are two other formats
        we've seen and must work around.

        (CASE 1)
        The anchor has multiple lines broken with <br> tag(s), and each
        line contains "<docket> <name>". In this case we need to combine
        the docket numbers and name strings respectively.
        [EXAMPLE: February 18, 2016 in nh_example_2.html]

        (CASE 2)
        The anchor has multiple lines broken with <br> tag(s), and the
        second line is a continuation of a long case name started on the first
        line.  So, the second line does not lead with a docket number, thus
        this line's string should be glued onto the <name> substring extracted
        from the previous line.
        [EXAMPLE: September 18, 2018 in nh_example_6.html]
        """
        pairs = []
        for anchor in self.html.xpath(self.link_path):
            i = 0
            dockets = []
            name_substrings = []
            for text in anchor.xpath('text()'):
                text = text.strip()
                match = self.link_text_regex.search(text)
                try:
                    docket = match.group(1)
                    dockets.append(docket)
                    name = match.group(2)
                    name = ' '.join(name.split())
                    name_substrings.append(name)
                    i += 1
                except AttributeError:
                    if i == 0:
                        # docket and name (root) should be contained in first substring
                        error = 'Unexpected anchor root string format: %s' % text
                        raise InsanityException(error)
                    # no docket in the substring, its a trailing name substring
                    # that they broke over multiple lines, so glue it to the
                    # previous name substring
                    name_substrings[i-1] += ' %s' % text
            pairs.append({
                'docket': ', '.join(dockets),
                'name': ' and '.join(name_substrings),
            })
        return pairs
