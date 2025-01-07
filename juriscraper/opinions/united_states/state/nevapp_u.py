"""Scraper for Nevada Supreme Court
CourtID: nev

History:
    - 2023-12-13: Updated by William E. Palin
"""
from juriscraper.AbstractSite import logger
from juriscraper.opinions.united_states.state import nev

class Site(nev.Site):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.court_id = self.__module__
        self.url = "https://publicaccess.nvsupremecourt.us/WebSupplementalAPI/api/COAUnpublishedOrders"
        self.search = "https://caseinfo.nvsupremecourt.us/public/caseSearch.do"
        self.status = "Unpublished"
        self.court_code = "10002"
        self.headers = {
            "Referer": "https://nvcourts.gov/",
            "XApiKey": "080d4202-61b2-46c5-ad66-f479bf40be11",
        }
        self.pdfurl = "https://publicaccess.nvsupremecourt.us/WebSupplementalAPI/api/urlRequest/doc/"

    def _process_html(self):
        """Process Nevada Case Opinions

        :return: None
        """
        for case in self.filtered_json:
            logger.info(f"fetching the details of the case with docket : {case['caseNumber']}")
            pdf_url = self.get_pdf_url(case['docurl'])
            self.cases.append(
                {
                    "name": case['caseTitle'],
                    "docket": [case['caseNumber']],
                    "date": case['date'],
                    "url": pdf_url,
                }
            )

    def get_class_name(self):
        return "nevapp_u"
