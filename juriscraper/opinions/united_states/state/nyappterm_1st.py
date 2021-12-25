# Scraper for New York Appellate Term 1st Dept.
# CourtID: nyappterm_1st
# Court Short Name: NY

from datetime import date, timedelta

from lxml.html import fromstring

from juriscraper.OpinionSiteLinear import OpinionSiteLinear


class Site(OpinionSiteLinear):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.court = "Appellate+Term,+1st+Dept"
        self.parameters = {
            "rbOpinionMotion": "opinion",
            "Pty": "",
            "and_or": "and",
            "dtStartDate": (date.today() - timedelta(days=30)).strftime(
                "%m/%d/%Y"
            ),
            "dtEndDate": date.today().strftime("%m/%d/%Y"),
            "court": "Appellate Term, 1st Dept",
            "docket": "",
            "judge": "",
            "slipYear": "",
            "slipNo": "",
            "OffVol": "",
            "Rptr": "",
            "OffPage": "",
            "fullText": "",
            "and_or2": "and",
            "Order_By": "Party Name",
            "Submit": "Find",
            "hidden1": "",
            "hidden2": "",
        }

        self.court_id = self.__module__
        self.method = "POST"
        self.url = "https://iapps.courts.state.ny.us/lawReporting/Search?searchType=opinion"

    def _process_html(self):
        self.request["session"].post(self.url, data=self.parameters)
        self.html = fromstring(self.request["response"].text)
        for row in self.html.xpath(".//table")[-1].xpath(".//tr")[1:]:
            docket = " ".join(row.xpath("./td[5]//text()"))
            self.cases.append(
                {
                    "name": row.xpath(".//td")[0].text_content(),
                    "date": row.xpath(".//td")[1].text_content(),
                    "url": row.xpath(".//a")[0].get("href"),
                    "status": "Published"
                    if "(U)" not in docket
                    else "Unpublished",
                    "docket": docket,
                }
            )
