import re
from datetime import date

from dateutil.rrule import MONTHLY, rrule

from juriscraper.OpinionSiteLinear import OpinionSiteLinear


class Site(OpinionSiteLinear):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        today = date.today()
        self.url = (
            "https://media.ca8.uscourts.gov/cgi-bin/opnByMM.pl?theMM=%02d&theYY=%s&A1=Get+Opinions"
            % (today.month, today.year)
        )
        self.court_id = self.__module__

        self.back_scrape_iterable = [
            i.date()
            for i in rrule(
                MONTHLY,
                dtstart=date(1995, 11, 1),
                until=date(2015, 1, 1),
            )
        ]
        self.request["verify"] = False

    def _process_html(self):
        for link in self.html.xpath('//a[contains(@href, "opndir")]'):
            url = link.get("href")
            text = link.xpath("following-sibling::text()")[0].strip()
            first_line = text.split("\n")[0]
            date_filed, case_name = first_line.strip().split(" ", 1)
            docket_number = ", ".join(re.findall(r"\d{2}-\d{4}", text))

            lower_court = ""
            court_match = re.search(r"U\.S\. District Court.+", text)
            if court_match:
                lower_court = court_match.group(0)

            doc_name = link.text_content().split(".")[0].lower()
            if "p" in doc_name:
                status = "Published"
            elif "u" in doc_name:
                status = "Unpublished"
            else:
                status = "Unknown"

            self.cases.append(
                {
                    "date": date_filed,
                    "docket": docket_number,
                    "url": url,
                    "status": status,
                    "name": case_name.strip(),
                    "lower_court": lower_court,
                }
            )

    def _download_backwards(self, d):
        """
        If an updated backscraper is needed in the future, this court
        updates the HTML with new values with a 4/5 months lag.
        Among the new values, I have seen the following fields we collect:
        per_curiam, judges and summaries are available
        """
        self.url = (
            "http://media.ca8.uscourts.gov/cgi-bin/opnByMM.pl?theMM=%02d&theYY=%s&A1=Get+Opinions"
            % (d.month, d.year)
        )
        self.html = self._download()
        self._process_html()
