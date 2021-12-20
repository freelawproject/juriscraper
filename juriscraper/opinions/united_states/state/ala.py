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
        self.url = html.xpath("//*[@id='FileTable']")[0].xpath(".//a/@href")[0]
        self.date = (
            html.xpath("//*[@id='FileTable']")[0]
            .xpath(".//a")[0]
            .text_content()
            .split(",", 1)[1]
            .strip()
        )
        self.pdf = self._get_parsed_pdf(self.url)

    def _get_url(self, page, word):
        for annot in page.annots:
            if bool(
                set(range(int(word["top"]), int(word["bottom"])))
                & set(range(int(annot["bottom"]), int(annot["top"])))
            ):
                if word["x0"] - 5 < annot["x0"] < word["x0"] + 5:
                    return annot["uri"]

    def _process_html(self) -> None:
        for page in self.pdf.pages:
            words = page.extract_words(
                keep_blank_chars=True, extra_attrs=["fontname", "size"]
            )
            between = None
            for word in words:
                if word["size"] == 14.00:
                    author = word["text"]
                    continue
                if word["size"] == 12.00 and word["x0"] < 100:
                    docket = word["text"]
                    between = True
                    continue
                if between:
                    case_info = word["text"]
                    continue
                if word["text"] == "OPINION":
                    case = {}
                    case["docket"] = docket
                    case["judge"] = author
                    case["name"] = case_info.split("  (")[0]
                    case["date"] = self.date.split(",", 1)[1].strip()
                    case["status"] = "Published"
                    case["url"] = self._get_url(page, word)
                    self.cases.append(case)
