# Author: Phil Ardery
# Contact: https://www.ndcourts.gov/contact-us
# Date created: 2019-02-28

from juriscraper.OpinionSite import OpinionSite
from juriscraper.lib.exceptions import InsanityException
from juriscraper.lib.string_utils import convert_date_string


class Site(OpinionSite):
    def __init__(self, *args, **kwargs):
        super(Site, self).__init__(*args, **kwargs)
        self.court_id = self.__module__
        self.url = "https://www.ndcourts.gov/supreme-court/recent-opinions?pageSize=100"
        self.cases = []

    def _process_html(self):
        for row in self.html.xpath('//table//div[@class="row"]'):
            case = self.case_fields_extract(row)
            self.case_fields_validate(case)
            case = self.case_fields_sanitize(case)
            self.cases.append(case)

    def case_fields_extract(self, row):
        text_lines = row.xpath("./div/p[1]/text()")
        text_lines = [
            l.strip() for l in text_lines if l.strip()
        ]  # Remove empty lines
        line_count = len(text_lines)
        return {
            "citation": text_lines[0],
            "docket": text_lines[1],
            "date": text_lines[2],
            "name": row.xpath(".//a")[0].text_content().strip(),
            "nature": text_lines[3],
            "judge": text_lines[4],
            "summary": " ".join(text_lines[5:line_count])
            if line_count > 5
            else "",
            "url": row.xpath(".//button/@onclick")[0].split("'")[1],
        }

    def case_fields_validate(self, case):
        if "ND" not in case["citation"]:
            raise InsanityException("Invalid citation: %s" % case["citation"])
        if not case["docket"].startswith("Docket No.:"):
            raise InsanityException(
                "Invalid docket raw string: %s" % case["docket"]
            )
        if not case["date"].startswith("Filing Date:"):
            raise InsanityException(
                "Invalid date string raw string: %s" % case["date"]
            )
        if not case["nature"].startswith("Case Type:"):
            raise InsanityException(
                "Invalid type raw string: %s" % case["nature"]
            )
        if not case["judge"].startswith("Author:"):
            raise InsanityException(
                "Invalid author raw string: %s" % case["judge"]
            )

    def case_fields_sanitize(self, case):
        for field in ["date", "docket", "judge", "nature"]:
            case[field] = case[field].split(":", 1)[1].strip()
        return case

    def _get_download_urls(self):
        return [case["url"] for case in self.cases]

    def _get_case_names(self):
        return [case["name"] for case in self.cases]

    def _get_case_dates(self):
        return [convert_date_string(case["date"]) for case in self.cases]

    def _get_docket_numbers(self):
        return [case["docket"] for case in self.cases]

    def _get_nature_of_suit(self):
        return [case["nature"] for case in self.cases]

    def _get_neutral_citations(self):
        return [case["citation"] for case in self.cases]

    def _get_judges(self):
        return [case["judge"] for case in self.cases]

    def _get_precedential_statuses(self):
        return ["Published"] * len(self.cases)

    def _get_summaries(self):
        return [case["summary"] for case in self.cases]
