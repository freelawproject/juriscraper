"""Scraper for Missouri
CourtID: mo
Court Short Name: MO
Author: Ben Cassedy
Date created: 04/27/2014
"""

from datetime import date, datetime

from juriscraper.OpinionSiteLinear import OpinionSiteLinear


class Site(OpinionSiteLinear):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.court_id = self.__module__
        self.court = "Supreme"
        # self.url = self.build_url()
        self.status = "Published"

    def build_url(self,year : int ):
        return f"https://www.courts.mo.gov/page.jsp?id=12086&dist=Opinions%20{self.court}&date=all&year={year}#all"

    def _process_html(self):
        for row in self.html.xpath("//div[@class='margin-bottom-15']"):
            date = row.xpath(".//input")[0].value
            for opinion in row.xpath(".//div[@class='list-group-item-text']"):
                links = opinion.xpath("a")
                if len(links) != 2:
                    continue
                url = opinion.xpath("a")[1].get("href")
                all_text = opinion.xpath(".//text()")
                case_metadata = [t.strip() for t in all_text if t.strip()]
                docket, _, name, _, author, _, vote = case_metadata
                dockets=docket.replace("_and_"," ")
                dockets=dockets.replace("_"," ")
                dockets=dockets.replace(":","")
                dock=dockets.split(" ")
                print(dock)
                self.cases.append(
                    {
                        "name": name,
                        "docket": dock,
                        "url": url,
                        "date": date,
                        "disposition": vote.split(".")[0].strip(),
                        "author": author,
                        "judge": vote.split(".", 1)[1].strip(),
                    }
                )

    def crawl_back(self,start: int , end : int):
        if(start == end):
            print("start and end year are same")
            self.url = self.build_url(start)
            self.html=self._download()
            self._process_html()
        else:
            while(start != end):
                print(f"start and end year are not same start year is {start} and end year is {end}")

                self.url =self.build_url(start)
                self.html = self._download()
                self._process_html()
                start += 1


    def crawling_range(self, start_date: datetime, end_date: datetime) -> int:
        self.crawl_back(start_date.year,end_date.year)

        for attr in self._all_attrs:
            self.__setattr__(attr, getattr(self, f"_get_{attr}")())

        self._clean_attributes()
        if "case_name_shorts" in self._all_attrs:
            self.case_name_shorts = self._get_case_name_shorts()
        self._post_parse()
        self._check_sanity()
        self._date_sort()
        self._make_hash()
        return len(self.cases)

    def get_court_type(self):
        return "state"

    def get_class_name(self):
        return "mo"

    def get_state_name(self):
        return "Missouri"

    def get_court_name(self):
        return "Supreme Court of Missouri"
