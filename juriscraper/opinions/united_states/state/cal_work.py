"""
Author: Michael Lissner
Date created: 2013-04-05
Revised by Taliah Mirmalek on 2014-02-07
Scraper for the Supreme Court of Arizona
CourtID: ariz
Court Short Name: Ariz.
"""
import re
from datetime import datetime

from juriscraper.OpinionSiteLinear import OpinionSiteLinear


class Site(OpinionSiteLinear):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.url = 'https://www.dir.ca.gov/wcab/wcab_enbanc.htm'
        # self.status = 'Unpublished'

    def _process_html(self, start :int , end :int) -> None:
        for table in self.html.xpath(".//table[@class='table table-striped w100pct']"):
            case_cell = table.xpath(".//tr[1]/td[1]")[0]
            lines = case_cell.xpath('.//text()')
            cleaned = ' '.join(line.strip() for line in lines if line.strip())
            pdf_url = case_cell.xpath("./a/@href")[0]
            date = table.xpath(".//tr[1]/td[2]/text()")[0]
            citation = table.xpath('.//tr[1]/td[3]/text()')[0]
            year = int(date[-4:])
            docket_text = ''.join(table.xpath('.//tr[2]/td//text()')).strip()
            dockets = re.findall(r'ADJ\d+', docket_text)
            if table.xpath('.//tr[4]/td/p/text()'):
                description = table.xpath('.//tr[4]/td/p/text()')[0]
            else:
                description = table.xpath('.//tr[4]/td/text()')[0]
            li_items = table.xpath('.//tr[4]/td/ol/li')
            clean_parties = []

            for li in li_items:
                full_text = ' '.join(li.xpath('.//text()')).strip()

                name_split = full_text.split(' - ADJ', 1)
                if len(name_split) == 2:
                    name_part = name_split[0].strip()
                    dockets_raw = 'ADJ' + name_split[1]
                    docket_numbers = re.findall(r'ADJ\d+', dockets_raw)
                    docket = ', '.join(docket_numbers)
                    clean_parties.append(f"{name_part} - {docket}")
                else:
                    clean_parties.append(full_text)
            party_lines = '\n'.join(clean_parties)
            party_lines=party_lines.replace("       "," ")

            full_description = f"{description}\n\n{party_lines}"

            if year < start or year > end:
                break
            self.cases.append(
                {
                    "date": date,
                    "docket": dockets,
                    "name": cleaned,
                    "url": pdf_url,
                    "citation":[citation],
                    "status":"Unpublished",
                    "summary":full_description
                }
            )


    def crawling_range(self, start_date: datetime, end_date: datetime) -> int:
        start = start_date.year
        end = end_date.year
        self.html  = self._download()
        self._process_html(start,end)

        for attr in self._all_attrs:
            self.__setattr__(attr, getattr(self, f"_get_{attr}")())

        self._clean_attributes()
        if "case_name_shorts" in self._all_attrs:
            self.case_name_shorts = self._get_case_name_shorts()
        self._post_parse()
        self._check_sanity()
        self._date_sort()
        self._make_hash()
        return 0

    def get_court_type(self):
        return "state"

    def get_court_name(self):
        return "California Workers Compensation Decisions"

    def get_state_name(self):
        return "California"

    def get_class_name(self):
        return "cal_work"
