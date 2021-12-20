"""
Scraper for Alabama Supreme Court
CourtID: ala
Court Short Name: Ala.
Author: William E. Palin
Court Contact:
Reviewer:
History:
 - 2021-12-19: Created.
"""
from typing import Dict

import pdfplumber

from juriscraper.OpinionSiteLinear import OpinionSiteLinear


class Site(OpinionSiteLinear):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.url = (
            "https://judicial.alabama.gov/decision/supremecourtdecisions"
        )
        self.court_id = self.__module__
        self.pdf = None

    def _download(self, request_dict={}):
        html = super()._download(request_dict)
        if self.test_mode_enabled:
            self.pdf = pdfplumber.open(
                "tests/examples/opinions/united_states/ala_example.pdf"
            )
            self.date = "December 10, 2021"
            return

        self.url = html.xpath("//*[@id='FileTable']")[0].xpath(".//a/@href")[0]
        self.date = (
            html.xpath("//*[@id='FileTable']")[0]
            .xpath(".//a")[0]
            .text_content()
            .split(",", 1)[1]
            .strip()
        )
        # Download the PDF binary and store it as a PDF Plumber object.
        self.pdf = self._get_parsed_pdf(self.url)

    def _get_url(self, page: pdfplumber.pdf.Page, word: Dict) -> str:
        """Check for a hyperlink in the location of the word OPINION

        We use the location data to determine if there is a hyperlink
        for the case.

        :param page: PDF Page
        :param word: The hyeprlink word
        :return: The URL of the annotation
        """
        for annot in page.annots:
            if bool(
                set(range(int(word["top"]), int(word["bottom"])))
                & set(range(int(annot["bottom"]), int(annot["top"])))
            ) and bool(
                set(range(int(word["x0"]), int(word["x1"])))
                & set(range(int(annot["x0"]), int(annot["x1"])))
            ):
                return annot["uri"]

    def _process_html(self) -> None:
        # This code uses the nice font size inforamtion to determine
        # the type of content as it paginates the PDF.
        # They may be difficult but they are at least consistent.
        for page in self.pdf.pages:
            words = page.extract_words(
                keep_blank_chars=True, extra_attrs=["fontname", "size"]
            )
            get_case_info = False
            for word in words:
                if word["size"] == 14.00:
                    author = word["text"]
                # x0 is the left side of the word
                if word["size"] == 12.00 and word["x0"] < 100:
                    docket = word["text"]
                    get_case_info = True
                    continue
                if get_case_info:
                    case_info = word["text"]
                    get_case_info = False
                    continue
                if word["text"] == "OPINION":
                    self.cases.append(
                        {
                            "docket": docket,
                            "judge": author,
                            "name": case_info.split("  (")[0],
                            "date": self.date,
                            "status": "Published",
                            "url": self._get_url(page, word),
                        }
                    )
