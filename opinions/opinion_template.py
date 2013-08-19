"""Scraper for [Full name of court]
CourtID: [unique abbreviation to be used by software/filesystem]
Court Short Name: [standard abbreviation used in citations]
Author:
Date created:
"""

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

            Note that relative URLs are made absolute by the GenericSite
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

      Remove this comment and any unused methods before submission
    """
    def _get_docket_numbers(self):
        """
          This is typically of the form ##-####
        """
        return None

    def _get_neutral_citations(self):
        """
          This is often of the form year, state abbreviation, sequential number
          as in '2013 Neb. 12' which would be the 12th opinion issued in 2013.
        """
        return None

    def _get_judges(self):
        """
          For the name of the judge authoring the lead opinion
        """
        return None

    def _get_lower_courts(self):
        """
          If the document is an opinion of an appellate court, then the court
          from which the case was appealed would go here. So, a 9th Circuit
          case might be appealed from the 'N.D. Cal.' which would go here.
        """
        return None

    def _get_nature_of_suit(self):
        """
          Some courts provide a NOS code or phrase giving the subject matter
          of the case, such as 'Contract' 'Civil Rights' 'Immigration' etc.
        """
        return None

    def _get_summaries(self):
        """
          Some courts provide a summary of the case or the opinion's holding.
        """
        return None

    def _get_west_citations(self):
        """
          You are unlikely to encounter these unless it's a backscraper because
          these citations only exist once the document is in a bound volume.
        """
        return None

    """
      Optional fields

      Remove this comment and any unused methods before submission
    """
    def _get_adversary_numbers(self):
        """
          Similar to a docket number, but found only in bankruptcy cases.
        """
        return None

    def _get_causes(self):
        """
          Some courts will give the plaintiff's or appellant's cause of action
          such as 'Employment' 'Trademark' etc.
        """
        return None

    def _get_dispositions(self):
        """
          Affirmed, Reversed, Vacated; if longer than a sentence, should
          probably use _get_summaries instead.
        """
        return None

    def _get_docket_attachment_numbers(self):
        """
          A document appears on a docket. Each line on the docket has a number.
          Item number 12, for example, might be a declaration with several
          attachments, numbered 1-5. That number, from 1-5, goes here.
        """
        return None

    def _get_docket_document_numbers(self):
        """
          A document appears on a docket. Each line on the docket has a number.
          Those numbers go here.
        """
        return None

    def _get_lower_court_judges(self):
        """
          If the document is an opinion of an appellate court, then the court
          from which the case was appealed is the lower court. So, a 9th Cir.
          case might be appealed from the N.D. Cal. and the judge from that
          court that handled the case would go here.
        """
        return None

    def _get_lower_court_numbers(self):
        """
          If the document is an opinion of an appellate court, then the court
          from which the case was appealed is the lower court. So, a 9th Cir.
          case might be appealed from the N.D. Cal. and the docket number or
          other relevant case numbers from that court would go here.
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
