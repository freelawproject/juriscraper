from datetime import datetime

from juriscraper.OpinionSiteLinear import OpinionSiteLinear


class Site(OpinionSiteLinear):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.court_id = self.__module__
        self.year = datetime.today().year
        self.url = f"https://www.courts.wa.gov/opinions/index.cfm?fa=opinions.byYear&fileYear={self.year}&crtLevel=S&pubStatus=PUB"
        self.status = "Published"

    def _process_html(self):
        for row in self.html.xpath('//tr/td[@valign="top"]/..')[::-1]:
            if len(row.xpath(".//td")) != 4:
                continue
            date, middle, name, op_type = row.xpath(".//td")
            self.cases.append(
                {
                    "date": date.text_content(),
                    "url": middle.xpath("a")[1].get("href"),
                    "name": name.text_content().replace("* ", ""),
                    "docket": middle.xpath("a")[0].text_content(),
                }
            )
