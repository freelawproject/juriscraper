# Author:
# Date created:

# import re
from datetime import date
from datetime import datetime
from lxml import html

from juriscraper.GenericSite import GenericSite
# from juriscraper.lib.string_utils import titlecase


class Site(GenericSite):
    def __init__(self):
        super(Site, self).__init__()
        self.court_id = self.__module__
        self.url = 'http://court-url.gov/some-path.html'

    '''
      Required fields - InsanityExceptions will be thrown if omitted.

      Remove this comment before submission.
    '''
    def _get_download_urls(self):
        """ This is an example of a basic piece of meta data accessible with a
            simple XPath query.

            On a good site, most of your methods will follow this pattern.
        """
        path = '//path/to/text/text()'
        return list(self.html.xpath(path))

    def _get_case_names(self):
        """ This example demonstrates how to extract text from an element that
            may contain other elements.

            For example, this will work well on something like:
               <strong>Nadim v. <em>Jenny</em></strong>

            Resulting in text like:
               Nadim v. Jenny

            Note that titlecase() should be used here in the case that the case
            names are provided in uppercase.
        """
        case_names = []
        for e in self.html.xpath('//path/to/an/element/p'):
            s = html.tostring(e, method='text', encoding='unicode')
            case_names.append(titlecase(s))
        return case_names

    def _get_case_dates(self):
        """ This is an example of a date field. Note that the format string
            will likely need to be updated to  match the date formats
            on the site you are scraping.
        """
        path = '//path/to/text/text()'
        return [datetime.strptime(date_string, '%m/%d/%Y').date()
                for date_string in self.html.xpath(path)]

    def _get_precedential_statuses(self):
        """ In most cases, this field should be normalized to either
            'Published' or 'Unpublished', as below.
        """
        statuses = []
        for e in self.html.xpath('//path/to/text/text()'):
            s = html.tostring(e, method='text', encoding='unicode')
            if 'Opinion' in s:
                statuses.append('Published')
            elif 'Nonprecedential' in s:
                statuses.append('Unpublished')
            else:
                statuses.append('Unknown')
        return statuses

    """
      High priority fields

      Remove this commend and any unused methods before submission
    """
    def _get_docket_numbers(self):
        return None

    def _get_neutral_citations(self):
        return None

    def _get_judges(self):
        return None

    def _get_lower_courts(self):
        return None

    def _get_nature_of_suit(self):
        return None

    def _get_summaries(self):
        return None

    def _get_west_citations(self):
        return None

    """
      Optional fields

      Remove this comment and any unused methods before submission
    """
    def _get_adversary_numbers(self):
        # Common in bankruptcy cases where there are adversary proceedings.
        return None

    def _get_causes(self):
        return None

    def _get_dispositions(self):
        return None

    def _get_docket_attachment_numbers(self):
        return None

    def _get_docket_document_numbers(self):
        return None

    def _get_lower_court_judges(self):
        return None

    def _get_lower_court_numbers(self):
        return None

    """
      Optional method used for downloading multiple pages of a court site.
    """
    def _download_backwards(self, date_str):
        """ This is a simple method that can be used to generate Site objects
            that can be used to paginate through a court's entire website.

            This method is usually called by a backscraper caller (see the
            one in CourtListener/alert/scrapers for details), and typically
            modifies aspects of the Site object's attributes such as Site.url.

            A simple example has been provided below. The idea is that the
            caller runs this method with a different variable on each iteration.
            That variable is often a date that is getting iterated or is simply
            a index (i), that we iterate upon.

            This can also be used to hold notes useful to future backscraper
            development.
        """
        self.url = 'http://example.com/new/url/%s' % date_str
        self.html = self._download()
