"""Scraper for Missouri
CourtID: mo
Court Short Name: MO
Author: Ben Cassedy
Date created: 04/27/2014
"""

from datetime import date

from juriscraper.OpinionSiteLinear import OpinionSiteLinear


class Site(OpinionSiteLinear):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.court_id = self.__module__
        self.court = "Supreme"
        self.url = self.build_url()
        self.status = "Published"

    def build_url(self):
        year = date.today().year
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
                self.cases.append(
                    {
                        "name": name,
                        "docket": docket[:-1],
                        "url": url,
                        "date": date,
                        "dispostion": vote.split(".")[0].strip(),
                        "judge": author,
                        "judges": vote.split(".", 1)[1].strip(),
                    }
                )
