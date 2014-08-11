"""Scraper for the Rhode Island Supreme Court
CourtID: ri
Court Short Name: R.I.
Author: Brian W. Carver
Date created: 2013-08-10
"""
from juriscraper.AbstractSite import InsanityException

import re
from datetime import datetime
from lxml import html

from juriscraper.OpinionSite import OpinionSite


class Site(OpinionSite):
    def __init__(self):
        super(Site, self).__init__()
        self.court_id = self.__module__
        # This court hears things from mid-September to end of June. This
        # defines the "term" for that year, which triggers the website updates.
        today = datetime.today()
        if today >= datetime(today.year, 9, 15):
            self.current_year = today.year
        else:
            self.current_year = today.year - 1
        self.url = 'http://www.courts.ri.gov/Courts/SupremeCourt/Opinions/Opinions%20%28{current}-{next}%29.aspx'.format(
            current=self.current_year,
            next=self.current_year + 1,
        )
        # The list of pages can be found here:
        # http://www.courts.ri.gov/Courts/SupremeCourt/Pages/Opinions%20and%20Orders%20Issued%20in%20Supreme%20Court%20Cases.aspx

        # This regex should be fairly clear, but the question mark at the end
        # might be confusing. That is there to make the date match optional,
        # because sometimes they forget it.
        self.regex = '(.*?)((?:Nos?\.)?\s+(?:\d{2,}-\d+,?\s?)+)(\(.*\))?'

    def _get_download_urls(self):
        path = "//table[@id = 'onetidDoclibViewTbl0']/tr[position() > 1]/td/a[child::span]/@href"
        return list(self.html.xpath(path))

    def _get_case_names(self):
        case_names = []
        path = "//table[@id = 'onetidDoclibViewTbl0']/tr[position() > 1]/td/a/span/text()"
        for s in self.html.xpath(path):
            case_name = re.search(self.regex, s, re.MULTILINE).group(1)
            case_names.append(case_name)
        return case_names

    def _get_precedential_statuses(self):
        return ['Published'] * len(self.case_names)

    def _get_case_dates(self):
        case_dates = []
        path = "//table[@id = 'onetidDoclibViewTbl0']/tr[position() > 1]/td/a/span/text()"
        previous = None
        error_count = 0
        for s in self.html.xpath(path):
            try:
                date_string = re.search(self.regex, s, re.MULTILINE).group(3)
                d = datetime.strptime(date_string.strip(), '(%B %d, %Y)').date()
                case_dates.append(d)
                previous = d
                error_count = 0
            except AttributeError:
                # Happens when the regex fails. Use the previous date and set
                # error_count back to zero.
                error_count += 1
                if error_count == 2:
                    raise InsanityException(
                        "Regex appears to be failing in Rhode Island")
                else:
                    case_dates.append(previous)
        return case_dates

    def _get_docket_numbers(self):
        docket_numbers = []
        path = "//table[@id = 'onetidDoclibViewTbl0']/tr[position() > 1]/td/a/span/text()"
        for s in self.html.xpath(path):
            dockets = re.search(self.regex, s, re.MULTILINE).group(2)
            #This page lists these about five different ways, normalizing:
            dockets = re.sub('Nos?\.', '', dockets)
            docket_numbers.append(dockets)
        return docket_numbers

    def _get_summaries(self):
        summaries = []
        path = "//table[@id = 'onetidDoclibViewTbl0']/tr[position() > 1]/td/div[@class = 'styleDescription']"
        for e in self.html.xpath(path):
            summaries.append(html.tostring(e, method='text', encoding='unicode'))
        return summaries
