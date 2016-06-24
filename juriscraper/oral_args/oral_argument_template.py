"""Scraper for [Full name of court]
CourtID: [unique abbreviation to be used by software/filesystem]
Court Short Name: [standard abbreviation used in citations]
Author:
Reviewer:
History:
  YYYY-MM-DD: Created by XXX
"""

from lxml import html
from juriscraper.OralArgumentSite import OralArgumentSite
from juriscraper.lib.string_utils import titlecase
from juriscraper.lib.string_utils import convert_date_string


class Site(OralArgumentSite):
    def __init__(self, *args, **kwargs):
        super(Site, self).__init__(*args, **kwargs)
        self.court_id = self.__module__
        self.url = 'http://court-url.gov/some-path.html'
        self.method = 'POST'
        self.uses_selenium = False
        # Complete this variable if you create a backscraper.
        self.back_scrape_iterable = None

    '''
      Required fields - InsanityExceptions will be thrown if omitted.

      Remove this comment before submission.
    '''
    def _get_download_urls(self):
        """ This is an example of a basic piece of meta data accessible with a
            simple XPath query.

            On a good site, most of your methods will follow this pattern.

            Note that relative URLs are made absolute by the AbstractSite
            object's cleanup routines, so doing so here is not needed.
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
            names are provided in uppercase. Use the titlecase function on
            cases where the name is provided in uppercase only.
        """
        case_names = []
        for e in self.html.xpath('//path/to/an/element/p'):
            s = html.tostring(e, method='text', encoding='unicode')
            case_names.append(titlecase(s))
        return case_names

    def _get_case_dates(self):
        """ This is an example of a date field. Note that the format string
            will likely need to be updated to  match the date formats
            on the site you are scraping. The datetime formats can be found
            here: http://docs.python.org/2/library/datetime.html
        """
        path = '//path/to/text/text()'
        return [convert_date_string(date_string) for date_string in
                self.html.xpath(path)]

    """
      High priority fields

      Remove this comment and any unused methods before submission
    """
    def _get_docket_numbers(self):
        """
          This is typically of the form ##-####
        """
        return None

    def _get_judges(self):
        """
          For the name of the judge authoring the lead opinion
        """
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
