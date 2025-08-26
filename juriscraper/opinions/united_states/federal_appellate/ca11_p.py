# Editor: mlr
# Maintenance log
#    Date     | Issue
# 2013-01-28  | InsanityException due to the court adding busted share links.
# 2014-07-02  | New website required rewrite.
# 2025-08-26  | Updated to use OpinionSiteLinear and added extract_from_text.


from juriscraper.lib.string_utils import clean_string
from juriscraper.OpinionSiteLinear import OpinionSiteLinear


class Site(OpinionSiteLinear):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.court_id = self.__module__
        self.url = "http://media.ca11.uscourts.gov/opinions/pub/logname.php"
        self.back_scrape_iterable = list(range(20, 10000, 20))
        self.should_have_results = True
        self.status = "Published"

    def _process_html(self):
        case_names = list(
            self.html.xpath("//tr[./td[1]/a//text()]/td[1]//text()")
        )
        download_urls = list(
            self.html.xpath("//tr[./td[1]/a//text()]/td[1]/a/@href")
        )
        case_dates = list(
            self.html.xpath("//tr[./td[1]/a//text()]/td[5]//text()")
        )
        docket_numbers = list(
            self.html.xpath("//tr[./td[1]/a//text()]/td[2]//text()")
        )
        nature_of_suit = list(
            self.html.xpath("//tr[./td[1]/a//text()]/td[4]//text()")
        )

        case_dates_cleaned = []
        for date_string in case_dates:
            s = clean_string(date_string)
            if s == "00-00-0000" and "begin=21160" in self.url:
                # Bad data found during backscrape.
                s = "12-13-2006"
            case_dates_cleaned.append(clean_string(s))

        for name, url, date, docket, nature in zip(
            case_names,
            download_urls,
            case_dates_cleaned,
            docket_numbers,
            nature_of_suit,
        ):
            self.cases.append(
                {
                    "name": clean_string(name),
                    "url": url,
                    "date": date,
                    "docket": clean_string(docket),
                    "status": "Published",
                    "nature_of_suit": clean_string(nature),
                }
            )

    def extract_from_text(self, scraped_text: str) -> dict:
        """Extract lower court from the scraped text.

        :param scraped_text: The text to extract from.
        :return: A dictionary with the metadata.
        """
        import re

        pattern = re.compile(
            r"""
            (?:
               Appeal(?:s)?\s+from\s+the\s+
              | Petition(?:s)?\s+for\s+Review\s+of\s+(?:a\s+)?Decision\s+of\s+the\s+
            )
            (?P<lower_court>[^.]+?)
            (?=\s*(?:\.|Nos?\.|USC|D.C.))
            """,
            re.X,
        )
        match = pattern.search(scraped_text)
        lower_court = (
            re.sub(r"\s+", " ", match.group("lower_court")).strip()
            if match
            else ""
        )
        return {
            "Docket": {
                "appeal_from_str": lower_court,
            }
        }

    def _download_backwards(self, n):
        self.url = f"http://media.ca11.uscourts.gov/opinions/pub/logname.php?begin={n}&num={n / 20 - 1}&numBegin=1"
        self.html = self._download()
        self._process_html()
