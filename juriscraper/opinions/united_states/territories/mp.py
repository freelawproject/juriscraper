"""Scraper for Supreme Court of Northern Mariana Islands
CourtID: mp
Court Short Name: NMI
Author: William Edward Palin
History:
  2023-01-21: Created by William Palin
"""

from datetime import date

from juriscraper.OpinionSiteLinear import OpinionSiteLinear


class Site(OpinionSiteLinear):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.court_id = self.__module__
        year = str(date.today().year)[-2:]
        self.url = f"https://www.cnmilaw.org/spm{year}.php#gsc.tab=0"
        self.status = "Published"

    def _process_html(self):
        for s in self.html.xpath(".//tr/td/.."):
            cells = s.xpath(".//td")
            judges = cells[3].text_content()
            judges = [
                j.replace(" Jr.", "Jr.").strip(" *") for j in judges.split(",")
            ]
            judges = [j.replace("Jr.", " Jr.") for j in judges]
            if ".pdf" not in s.xpath(".//td/a/@href")[0]:
                # Check for any opinions. Helpful for new year turn over
                continue
            if "*" not in cells[3].text_content():
                author = "Per Curiam"
            else:
                author = [
                    j for j in cells[3].text_content().split(",") if "*" in j
                ][0].strip("*")
            self.cases.append(
                {
                    "name": cells[0].text_content(),
                    "citation": cells[1].text_content(),
                    "date": cells[2].text_content(),
                    "judges": judges,
                    "author": author,
                    "url": s.xpath(".//td/a/@href")[0],
                    "docket": "",
                }
            )
