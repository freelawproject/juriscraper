"""
Court Contact: https://www.supremecourt.gov/contact/contact_webmaster.aspx
"""


from datetime import date

from juriscraper.AbstractSite import logger
from juriscraper.lib.exceptions import InsanityException
from juriscraper.lib.string_utils import convert_date_string
from juriscraper.OpinionSite import OpinionSite


class Site(OpinionSite):
    required_headers = ["Date", "Docket", "Name", "J."]
    expected_headers = required_headers + ["Revised", "R-", "Pt."]
    justices = {
        "A": "Samuel Alito",
        "AB": "Amy Coney Barrett",
        "AS": "Antonin Scalia",
        "B": "Stephen Breyer",
        "BK": "Brett Kavanaugh",
        "D": "Decree",
        "DS": "David Souter",
        "EK": "Elana Kagan",
        "G": "Ruth Bader Ginsburg",
        "JS": "John Paul Stephens",
        "K": "Anthony Kennedy",
        "NG": "Neil Gorsuch",
        "PC": "Per Curiam",
        "R": "John G. Roberts",
        "SS": "Sonia Sotomayor",
        "T": "Clarence Thoma",
    }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.court_id = self.__module__
        self.yy = self._get_current_term()
        self.back_scrape_iterable = list(range(6, int(self.yy) + 1))
        self.url_base = "https://www.supremecourt.gov/opinions"
        self.path_table = "//table[@class='table table-bordered']"
        self.path_row = f"{self.path_table}/tr[position() > 1]"
        self.precedential = "Published"
        self.court = "slipopinion"
        self.headers = False
        self.url = False
        self.headers = []
        self.cases = []

    @staticmethod
    def _get_current_term():
        """The URLs for SCOTUS correspond to the term, not the calendar.

        The terms kick off on the first Monday of October, so we use October 1st
        as our cut off date.
        """
        today = date.today()
        term_cutoff = date(today.year, 10, 1)
        if today < term_cutoff:
            # Haven't hit the cutoff, return previous year.
            return int(today.strftime("%y")) - 1  # y3k bug!
        else:
            return today.strftime("%y")

    def _download(self, request_dict={}):
        if not self.test_mode_enabled():
            self.set_url()
        html = super()._download(request_dict)
        self.extract_cases_from_html(html)
        return html

    def set_url(self):
        self.url = f"{self.url_base}/{self.court}/{self.yy}"

    def set_table_headers(self, html):
        # Do nothing if table is missing
        if html.xpath(self.path_table):
            path = f"{self.path_table}//th"
            self.headers = [
                cell.text_content().strip() for cell in html.xpath(path)
            ]
            # Ensure that expected/required headers are present
            if not set(self.required_headers).issubset(self.headers):
                raise InsanityException("Required table column missing")

    def extract_cases_from_html(self, html):
        self.set_table_headers(html)
        for row in html.xpath(self.path_row):
            case = self.extract_case_data_from_row(row)
            if case:
                # Below will raise key error is new judge key encountered (new SC judge appointed)
                case["judge"] = self.justices[case["J."]] if case["J."] else ""
                self.cases.append(case)
                for revision_data in case["revisions"]:
                    revision = case.copy()
                    revision["Date"] = revision_data["date_string"]
                    revision["Name_Url"] = revision_data["href"]
                    self.cases.append(revision)

    def extract_case_data_from_row(self, row):
        cell_index = 0
        case = {"revisions": []}
        # Process each cell in row
        for cell in row.xpath("./td"):
            text = cell.text_content().strip()
            # Skip rows with blank first cell
            if cell_index == 0 and not text:
                break
            label = self.headers[cell_index]
            if label in ["R-", "Pt."]:
                # Ignore some columns that we don't need
                pass
            elif label == "Revised":
                # It is possible for an opinion to have
                # multiple revisions, so we need to iterate
                # over the links the the cell
                for anchor in cell.xpath("a"):
                    case["revisions"].append(
                        {
                            "href": anchor.xpath("@href")[0],
                            "date_string": anchor.text_content(),
                        }
                    )
            else:
                # Handle normal data cells
                case[label] = text
                href = cell.xpath("./a/@href")
                if href:
                    case[f"{label}_Url"] = href[0]
            cell_index += 1
        return case

    def _get_case_names(self):
        return [case["Name"] for case in self.cases]

    def _get_download_urls(self):
        return [case["Name_Url"] for case in self.cases]

    def _get_case_dates(self):
        return [convert_date_string(case["Date"]) for case in self.cases]

    def _get_docket_numbers(self):
        return [case["Docket"] for case in self.cases]

    def _get_judges(self):
        return [case["judge"] for case in self.cases]

    def _get_precedential_statuses(self):
        return [self.precedential] * len(self.cases)

    def _download_backwards(self, d):
        self.yy = str(d if d >= 10 else f"0{d}")
        logger.info(f"Running backscraper for year: 20{self.yy}")
        self.html = self._download()
