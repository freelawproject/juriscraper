import re

from juriscraper.lib.string_utils import convert_date_string
from juriscraper.OpinionSite import OpinionSite


class Site(OpinionSite):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.court_id = self.__module__
        self.court_code = "S"

    def _download(self, request_dict={}):
        if not self.test_mode_enabled():
            self.url = self.build_url()
        return super()._download(request_dict)

    def build_url(self):
        return (
            "http://www.courts.ca.gov/cms/opinions.htm?Courts=%s"
            % self.court_code
        )

    def _get_case_names(self):
        case_names = []
        for cell in self.html.xpath("//table/tr/td[3]"):
            name = cell.text_content()
            date_regex = re.compile(r" \d\d?/\d\d?/\d\d| filed")
            if "P. v. " in date_regex.split(name)[0]:
                case_names.append(
                    date_regex.split(name)[0].replace("P. ", "People ")
                )
            else:
                case_names.append(date_regex.split(name)[0])
        return case_names

    def _get_download_urls(self):
        return [
            t
            for t in self.html.xpath(
                "//table/tr/td[2]/a/@href[contains(.,'PDF')]"
            )
        ]

    def _get_case_dates(self):
        path = "//table/tr/td[1]/text()"
        return [
            convert_date_string(date_string)
            for date_string in self.html.xpath(path)
        ]

    def _get_docket_numbers(self):
        return [t for t in self.html.xpath("//table/tr/td[2]/text()[1]")]

    def _get_precedential_statuses(self):
        return ["Published"] * len(self.case_names)
