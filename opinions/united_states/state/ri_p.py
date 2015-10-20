"""Scraper for the Rhode Island Supreme Court
CourtID: ri
Court Short Name: R.I.
Author: Brian W. Carver
Date created: 2013-08-10
"""
from datetime import datetime

from juriscraper.AbstractSite import InsanityException
from juriscraper.OpinionSite import OpinionSite
import re


class Site(OpinionSite):
    def __init__(self, *args, **kwargs):
        super(Site, self).__init__(*args, **kwargs)
        self.court_id = self.__module__
        # This court hears things from mid-September to end of June. This
        # defines the "term" for that year, which triggers the website updates.
        today = datetime.today()
        if today >= datetime(today.year, 9, 15):
            self.current_year = today.year
        else:
            self.current_year = today.year - 1
        self.url = 'http://www.courts.ri.gov/Courts/SupremeCourt/Pages/Opinions/Opinions{current}-{next}.aspx'.format(
            current=self.current_year,
            next=self.current_year + 1,
        )

        self.cached_records = None

        # The list of pages can be found here:
        # http://www.courts.ri.gov/Courts/SupremeCourt/Pages/Opinions%20and%20Orders%20Issued%20in%20Supreme%20Court%20Cases.aspx

        # This regex should be fairly clear, but the question mark at the end
        # might be confusing. That is there to make the date match optional,
        # because sometimes they forget it.
        self.regex = '(.*?)((?:Nos?\.)?\s+(?:\d{2,}[-,]\d+,?\s?)+)(\(.*\)?)?'

    @staticmethod
    def _normalize_dockets(dockets):
        #This page lists these about five different ways, normalizing:
        dockets = re.sub(r'Nos?\.', '', dockets)

        result = []
        for docket in dockets.split(", "):
            docket = docket.strip()
            if re.match(r"^\d+$", docket): # number
                result.append(docket)
            elif re.match(r"^\d+\-\d+$", docket): # number-number
                result.append(docket)
            elif re.match(r"^\d+\,\d+$", docket): # number,number
                # fix the docket number
                docket = docket.replace(",", "-")
                result.append(docket)
            else:
                raise InsanityException("Unknown docket number format '%s'"
                                        % (docket,))

        # reassemble the docket numbers into one string
        return ", ".join(result)

    def _do_load(self):
        results = []
        path = "//table[@id = 'onetidDoclibViewTbl0']/tr[position() > 1]"
        trs = list(self.html.xpath(path))

        # table structure:
        #   <tr> - contains case name, docket number, date and pdf link
        #   <tr> - contains case summary
        #   <tr> - contains a one-pixel gif

        # take the first two <tr> from each triplet
        for tr1, tr2 in zip(trs, trs[1:])[::3]:
            td1 = tr1.xpath("./td[1]/text()")[0]
            href = tr1.xpath("./td[2]/a/@href")[0]
            text = tr2.xpath("./td/div/text()")

            if not re.match(self.regex, td1):
                # regex to parse date formatted as '(March 30, 2015)'
                date_regex = r"^\(\w+\s+\d+\,\s+\d+\)$"
                # Special case 1:
                #   td1 contains only a date, matching date_regex
                #   first line of summary contains case name with docket number
                if re.match(date_regex, td1) and re.match(self.regex, text[0]):
                    search = re.search(self.regex, text[0], re.MULTILINE)
                    case_name = search.group(1)
                    dockets = search.group(2)
                    dockets = self._normalize_dockets(dockets)
                    date_string = td1.strip()
                    case_date = datetime.strptime(date_string,
                                                  '(%B %d, %Y)').date()
                    results.append({'date' : case_date,
                                    'url' : href,
                                    'docket' : dockets,
                                    'summary' : "\n".join(text[1:]),
                                    'case_name' : case_name})
                else:
                    # Special case 2:
                    # td1 contains a very long case name
                    #     docket number is missing
                    #     date is missing
                    link_text = tr1.xpath("./td[2]/a/text()")[0]
                    # use link text as docket number
                    link_text = self._normalize_dockets(link_text)
                    # use date from previous record
                    results.append({'date' : results[-1]['date'],
                                    'url' : href,
                                    'docket' : link_text,
                                    'summary' : "\n".join(text),
                                    'case_name' : case_name})
            else:
                search = re.search(self.regex, td1, re.MULTILINE)
                case_name = search.group(1)
                dockets = search.group(2)
                dockets = self._normalize_dockets(dockets)
                date_string = search.group(3)
                if date_string:
                    date_string = date_string.strip()
                    # remove parentheses
                    if date_string[0] == '(':
                        date_string = date_string[1:]
                    if date_string[-1] == ')':
                        date_string = date_string[:-1]
                    case_date = datetime.strptime(date_string, '%B %d, %Y').date()
                else:
                    # if no date, use date from previous record
                    case_date = results[-1]['date']
                results.append({'date' : case_date,
                                'url' : href,
                                'docket' : dockets,
                                'summary' : "\n".join(text),
                                'case_name' : case_name})
        return results

    def _load(self):
        if self.cached_records is None:
            self.cached_records = self._do_load()
        return self.cached_records

    def _filter(self, key):
        r = []
        for d in self._load():
            if d.get(key) is not None:
                r.append(d[key])
        return r

    def _get_download_urls(self):
        return self._filter('url')

    def _get_case_names(self):
        return self._filter('case_name')

    def _get_precedential_statuses(self):
        return ['Published'] * len(self.case_names)

    def _get_case_dates(self):
        return self._filter('date')

    def _get_docket_numbers(self):
        return self._filter('docket')

    def _get_summaries(self):
        return self._filter('summary')
