"""Scraper for Patent Trial and Appeals Board
CourtID: ptab
Court Short Name: P.T.A.B.
Author: Varun Iyer
Reviewer:
History:
  2019-08-01: Created by Varun Iyer
"""


import re
from lxml import html
from juriscraper.OpinionSite import OpinionSite
from juriscraper.lib.string_utils import convert_date_string
from juriscraper.lib.exceptions import InsanityException, ParsingException


class Site(OpinionSite):
    def __init__(self, *args, **kwargs):
        super(Site, self).__init__(*args, **kwargs)
        self.court_id = self.__module__
        self.url = 'https://www.uspto.gov/patents-application-process/patent-trial-and-appeal-board/precedential-informative-decisions'
        self.case_types = ['Precedential', 'Informative']
        self.cases = {}

    def _process_html(self):
        path = '//a[contains(./@href, ".pdf")]'
        for link in self.html.xpath(path):
            case = {}
            if len(link.text.strip()) == 0:
                # There seems to be some cases that are pdf-linked more than once, with the second link blank
                continue
            # text of case info apart from name
            utext = link.getparent().text_content()[len(link.text):]
            text = utext.encode("ascii", "replace");
            # date
            date = ""
            date_match = re.search("(\([a-zA-Z]+[^\w]{0,3}\d\d?. \d{4}\))|(\(\d{4}\))", utext)
            if date_match is not None:
                date = date_match.group(0).strip("()") 
            else:
                raise ParsingException("Date regexp failed on text" + text)
            # precedent
            header = link.getparent().getparent().getprevious().text
            precedential = 'Unpublished'
            if 'Precedential' in header:
                precedential = 'Published'
            # docket numbers 
            docket_match = re.search("(\d{2,4}-\d{4,6})|(\d{3},[0-9|A-Z]{3})|(\dx{2},x{3})", utext)
            docket = ""
            paper_match = re.search("Paper \d+", utext)
            if docket_match is not None:
                docket = docket_match.group(0)
                if paper_match is not None:
                    docket = "{} ({})".format(docket, paper_match.group(0))
            else:
                raise ParsingException("Docket No. Regexp failed on text" + text)
            # summary 
            # use unicode, there are a lot of section codes
            summary_match = re.search("\[.*\]", utext)
            summary = ""
            if summary_match is not None:
                summary = summary_match.group(0).strip("[]")
            else:
                ParsingException("Summary regexp failed on text {}".format(text))

            # We sometimes have repeats on this page, so dict
            self.cases[docket] = {
                "name": link.text,
                "url": link.get('href'),
                "date": convert_date_string(date),
                "precedential": precedential,
                "docket": docket,
                "summary": summary
            }
         
    def _get_download_urls(self):
        return [case["url"] for case in self.cases.itervalues()]

    def _get_case_names(self):
        return [case["name"] for case in self.cases.itervalues()]

    def _get_case_dates(self):
        return [case["date"] for case in self.cases.itervalues()]

    def _get_precedential_statuses(self):
        return [case["precedential"] for case in self.cases.itervalues()]

    def _get_docket_numbers(self):
        return [case["docket"] for case in self.cases.itervalues()]

    def _get_summaries(self):
        return [case["summary"] for case in self.cases.itervalues()]
