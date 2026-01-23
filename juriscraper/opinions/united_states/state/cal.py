import re

from juriscraper.OpinionSiteLinear import OpinionSiteLinear


class Site(OpinionSiteLinear):
    court_code = "S"
    division = ""
    date_regex = re.compile(r" \d\d?/\d\d?/\d\d| filed")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.court_id = self.__module__
        self.url = f"https://www.courts.ca.gov/cms/opinions.htm?Courts={self.court_code}"
        self.status = "Published"
        self.request["verify"] = False
        self.should_have_results = True

    def _process_html(self) -> None:
        for row in self.html.xpath("//table/tr[not(th)]"):
            name = row.xpath(".//*[@class='op-title']/text()")[0]

            split = self.date_regex.split(name)[0]
            if "P. v. " in split:
                case_name = split.replace("P. ", "People ")
            else:
                case_name = split

            url = row.xpath(".//a[@class='op-link']/@href")[0]
            date_filed = row.xpath(".//*[@class='op-date']/text()")[0]
            docket = row.xpath(".//*[@class='op-case']/text()")[0]
            case = {
                "name": case_name,
                "url": url,
                "date": date_filed,
                "docket": docket,
            }
            if self.division:
                case["division"] = self.division

            self.cases.append(case)

    def extract_from_text(self, scraped_text: str) -> dict:
        """Extract lower court and case number from the scraped text.

        :param scraped_text: The text to extract from.
        :return: A dictionary with the metadata.
        """
        pattern = re.compile(
            r"S\d+\s*\n"
            r"(?P<lower_court>.+?)\s*$"
            r"(\s*\n\s*)"
            r"(?P<lower_court_number>[A-Z0-9]{4,})\s*$",
            re.MULTILINE,
        )

        lower_court = ""
        lower_court_number = ""

        if match := pattern.search(scraped_text):
            lower_court = re.sub(
                r"\s+", " ", match.group("lower_court")
            ).strip()
            lower_court_number = match.group("lower_court_number").strip()

        result: dict[str, dict] = {}
        if lower_court or lower_court_number:
            if lower_court:
                result["Docket"] = {}
                result["Docket"]["appeal_from_str"] = lower_court
            if lower_court_number:
                result["OriginatingCourtInformation"] = {}
                result["OriginatingCourtInformation"]["docket_number"] = (
                    lower_court_number
                )

        return result
