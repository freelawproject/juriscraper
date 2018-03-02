"""
Auth: Jordan Atanasov <jordan.atanasov@commetric.com>
History:
    2012-05-07: Written by Jordan.
    2012-07-06: Updated by mlr to only get the first ten items.
    2015-07-28: Updated by m4h7 to have improved xpaths.
        Notes: Only queries first ten dates. Beyond that, they get messy.
    2017-01-11: Updated by arderyp to not suppress opinions under
        date range headings.  We'v added not logic to OpinionSite
        to handle estimated dates, and are now flagging these
        examples as such
"""

import datetime
from juriscraper.OpinionSite import OpinionSite
from juriscraper.lib.string_utils import convert_date_string, split_date_range_string, normalize_dashes


class Site(OpinionSite):
    url_court_id = 'sp'

    def __init__(self, *args, **kwargs):
        super(Site, self).__init__(*args, **kwargs)
        self.url = 'https://public.courts.alaska.gov/web/appellate/%s.htm' % self.url_court_id
        self.court_id = self.__module__
        self.date_string_path = '//h4'
        self.sub_opinion_path = './following-sibling::ul[1]//a/em'

    def _get_case_names(self):
        path = "//ul/li[descendant::a/em]//em/text()"
        return [t for t in self.html.xpath(path)]

    def _get_download_urls(self):
        path = "//ul/li/a[child::em]/@href"
        return [h for h in self.html.xpath(path)]

    def _get_case_dates(self):
        dates = []
        for element in self.html.xpath(self.date_string_path):
            # Determine the number of opinions below the
            # date and add them all to the date list.
            count = len(element.xpath(self.sub_opinion_path))
            # Handle different date formats
            date_string = element.text_content().strip()
            try:
                # Normal date
                date = convert_date_string(date_string)
            except ValueError:
                # It a date range string like 'January - March 2016'
                # return the middle date, unless its in the future
                # in which case return today's date
                middle_date = split_date_range_string(date_string)
                date = min(datetime.date.today(), middle_date)
            dates.extend([date] * count)
        return dates

    def _get_docket_numbers(self):
        path = "//ul/li[descendant::a/em]/text()[1]"
        return [t for t in self.html.xpath(path)]

    def _get_precedential_statuses(self):
        return ["Published"] * len(self.case_names)

    def _get_date_filed_is_approximate(self):
        approximations = []
        for element in self.html.xpath(self.date_string_path):
            count = len(element.xpath(self.sub_opinion_path))
            date_string = normalize_dashes(element.text_content())
            approximation = True if '-' in date_string else False
            approximations.extend([approximation] * count)
        return approximations
