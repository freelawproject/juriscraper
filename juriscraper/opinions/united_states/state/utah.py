from datetime import datetime

from juriscraper.OpinionSite import OpinionSite


class Site(OpinionSite):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.url = "http://www.utcourts.gov/opinions/supopin/index.htm"
        self.court_id = self.__module__

    def _get_case_names(self):
        return [
            name
            for name in self.html.xpath(
                '/html/body//div[@id="content"]//p[a[@class="bodylink"]]/a/text()'
            )
        ]

    def _get_download_urls(self):
        return [
            t
            for t in self.html.xpath(
                '/html/body//div[@id="content"]//p[a[@class="bodylink"]]/a/@href'
            )
        ]

    def _get_docket_numbers(self):
        docket_numbers = []
        for text in self.html.xpath(
            '/html/body//div[@id="content"]//p[a[@class="bodylink"]]/text()'
        ):
            try:
                parts = text.strip().split(", ")
                docket_numbers.append(parts[1])
            except IndexError:
                # Happens in whitespace-only text nodes.
                continue
        return docket_numbers

    def _get_case_dates(self):
        dates = []
        for text in self.html.xpath(
            '/html/body//div[@id="content"]//p[a[@class="bodylink"]]/text()'
        ):
            parts = text.strip().split(", ")
            try:
                caseDate = f"{parts[-3]}, {parts[-2]}"
                dates.append(datetime.strptime(caseDate, "Filed %B %d, %Y"))
            except IndexError:
                # Happens in whitespace-only text nodes.
                continue
        return dates

    def _get_precedential_statuses(self):
        return ["Published"] * len(self.case_names)

    def _get_citations(self):
        neutral_citations = []
        for text in self.html.xpath(
            '/html/body//div[@id="content"]//p[a[@class="bodylink"]]/text()'
        ):
            try:
                parts = text.strip().split(", ")
                if parts[-1]:
                    neutral_citations.append(parts[-1])
            except IndexError:
                # Happens in whitespace-only text nodes.
                continue
        return neutral_citations
