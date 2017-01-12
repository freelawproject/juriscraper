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
from juriscraper.AbstractSite import InsanityException
from juriscraper.lib.string_utils import convert_date_string, standardize_dashes


class Site(OpinionSite):
    def __init__(self, *args, **kwargs):
        super(Site, self).__init__(*args, **kwargs)
        self.url = 'http://www.courtrecords.alaska.gov/webdocs/opinions/sp.htm'
        self.court_id = self.__module__
        self.date_string_path = '//h4'
        self.sub_opinion_path = './following-sibling::ul[1]//a/em'

    def _get_case_names(self):
        return [e for e in self.html.xpath("//ul/li[descendant::a/em]//em/text()")]

    def _get_download_urls(self):
        return [h for h in self.html.xpath("//ul/li/a[child::em]/@href")]

    def _get_case_dates(self):
        dates = []
        for element in self.html.xpath(self.date_string_path):
            date_string = element.text_content().strip()
            try:
                date = convert_date_string(date_string)
            except ValueError:
                date = self.get_estimate_date(date_string)
            # Determine the number of opinions below the
            # date and add them all to the date list.
            count = len(element.xpath(self.sub_opinion_path))
            dates.extend([date] * count)
        return dates

    def _get_docket_numbers(self):
        return [t for t in self.html.xpath("//ul/li[descendant::a/em]/text()[1]")]

    def _get_precedential_statuses(self):
        return ["Published"] * len(self.case_names)

    def _get_date_filed_is_approximate(self):
        approximations = []
        for element in self.html.xpath(self.date_string_path):
            count = len(element.xpath(self.sub_opinion_path))
            date_string = standardize_dashes(element.text_content())
            approximation = True if '-' in date_string else False
            approximations.extend([approximation] * count)
        return approximations

    def get_estimate_date(self, date_string):
        """Return 1st of first month in range (i.e. January 1st 2016
        if range string is 'January - March 2016'). If said date is
        in the past, return today's date instead.
        """
        date_string = standardize_dashes(date_string)
        parts = date_string.split()
        if '-' in date_string and len(parts) == 4:
            estimate_string = '%s 1, %s' % (parts[0], parts[3])
            estimate_date = convert_date_string(estimate_string)
            return min(datetime.date.today(), estimate_date)
        else:
            raise InsanityException('Unrecognized date format: "%s"' % date_string)
