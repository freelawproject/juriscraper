"""Scraper for Colorado Appeals Court
CourtID: coloctapp
Court Short Name: Colo. Ct. App.

History:
    - 2022-01-31: Updated by William E. Palin
    - 2023-01-05: Updated by William E. Palin
"""


import datetime
import re

from lxml.html import fromstring

from juriscraper.opinions.united_states.state import colo


class Site(colo.Site):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.court_id = self.__module__
        self.month = datetime.date.today().month
        self.year = datetime.date.today().year
        self.url = f"https://www.courts.state.co.us/Courts/Court_of_Appeals/Case_Announcements/Index.cfm?year={self.year}&month={self.month}&Submit=Go"

    def _process_html(self):
        if not self.test_mode_enabled():
            self.initiate_webdriven_session()

        if not self.test_mode_enabled():
            links = self.html.xpath(".//a[@class='touchable-link']")
        else:
            links = ["fake_link"]

        for link in links:
            if self.test_mode_enabled():
                super()._download()
                date_filed = "December 29, 2022"
            else:
                date_filed = link.text_content()
                self.webdriver.get(link.get("href"))
                # Wait for pdf to render
                self.webdriver.implicitly_wait(10000)
                # And click next twice to make sure we fully render the PDF content
                self.find_element_by_id("next").click()
                self.find_element_by_id("next").click()
                self.html = fromstring(self.webdriver.page_source)

            pattern = r"(2022COA\d+)\n(.*?)\n(Division \w+)"
            urls_to_add = []
            for pg in self.html.xpath(".//div[@class='page']"):
                if not pg.xpath(".//span[@role='link']/span/@aria-owns"):
                    continue
                anno_ids = pg.xpath(".//span[@role='link']/span/@aria-owns")
                for anno_id in anno_ids:
                    urls = pg.xpath(
                        f"//a[@id='pdfjs_internal_id_{anno_id}']/@href"
                    )
                    if urls:
                        url = urls[0]
                        if url not in urls_to_add:
                            urls_to_add.append(url)
                pg_content = []
                for element in pg.xpath(".//span"):
                    if element.get("class") != "markedContent":
                        continue
                    pg_content.append(element.text_content())
                pg_text = "\n".join(pg_content)
                for match in re.finditer(pattern, pg_text, re.DOTALL):
                    citation = match.groups()[0]
                    case_name = self.get_case_name(match.groups()[1])
                    url = urls_to_add.pop(0)
                    docket = url.split("/")[-1][:-4]
                    self.cases.append(
                        {
                            "date": date_filed,
                            "name": case_name,
                            "docket": docket,
                            "status": "Published",
                            "url": url,
                            "citation": citation,
                        }
                    )

        if not self.test_mode_enabled():
            self.webdriver.quit()

    def get_case_name(self, page_content) -> str:
        """Get case name from page content

        :param pg: List of text
        :return: Cleaned case name
        """
        start = False
        content = []
        for row in page_content.split("\n"):
            if not row.strip():
                continue
            no_go_words = [
                "Plaintiff",
                "Appellee",
                "Defendant",
                "Intervenor",
                "Appellant",
            ]
            if any(word in row for word in no_go_words):
                continue
            m = re.findall(r"Honorable .*, Judge", row)
            if m:
                start = True
                continue
            m = re.findall(r"[A-Z ,]{5,}", row)
            if m and m[0] == row:
                start = False
            if not start:
                continue
            content.append(row.strip(","))
        case_name = " ".join(content)
        return case_name
