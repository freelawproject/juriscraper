"""Scraper for Colorado Supreme Court
CourtID: colo
Court Short Name: Colo.
Author: Philip Ardery
Reviewer: mlr
Date created: 2016-06-03
Contact: Email "Internet and Technology" staff listed at http://www.cobar.org/staff
         they usually fix issues without responding to the emails directly. You can
         also try submitting the form here: http://www.cobar.org/contact
History:
    - 2022-01-31: Updated by William E. Palin
    - 2023-01-05: Updated by William E. Palin
"""
import datetime
import re

from lxml.html import fromstring, tostring

from juriscraper.OpinionSiteLinearWebDriven import OpinionSiteLinearWebDriven


class Site(OpinionSiteLinearWebDriven):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.court_id = self.__module__
        self.year = datetime.date.today().year
        self.month = datetime.date.today().month
        self.url = f"https://www.courts.state.co.us/Courts/Supreme_Court/Case_Announcements/Index.cfm?year={self.year}&month={self.month}&Submit=Go"
        self.uses_selenium = True

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
                date_filed = "December 19, 2022"
            else:
                date_filed = link.text_content()
                self.webdriver.get(link.get("href"))
                # Wait for pdf to render
                self.webdriver.implicitly_wait(10000)
                # And click next twice to make sure we fully render the PDF content
                self.find_element_by_id("next").click()
                self.find_element_by_id("next").click()

                self.html = fromstring(self.webdriver.page_source)

            for pg in self.html.xpath(".//div[@class='page']"):
                if not pg.xpath(".//span[@role='link']/span/@aria-owns"):
                    continue
                anno_id = pg.xpath(".//span[@role='link']/span/@aria-owns")[0]
                pg_content = []
                for element in pg.xpath(".//span"):
                    if element.get("class") == "markedContent":
                        continue
                    pg_content.append(element.text_content())
                pg_text = " ".join(pg_content)

                case_name = self.get_case_name(pg)
                citation = re.findall(r"20\d{2} CO \d{1,3}M?", pg_text)
                if not citation:
                    # This is how we identify a page with an opinion
                    continue
                citation = citation[0]
                judges = ""
                m = re.findall(r"JUSTICE\s+\b([\wÁ]+)\b", pg.text_content())
                if m:
                    judges = ", ".join(m).replace("Á", "A")

                urls = pg.xpath(
                    f"//a[@id='pdfjs_internal_id_{anno_id}']/@href"
                )
                if not urls:
                    # One time an opinion wasn't linked.
                    continue
                url = urls[0]
                if "Opinions" not in url:
                    continue
                docket = url.split("/")[-1][:-4]

                self.cases.append(
                    {
                        "date": date_filed,
                        "name": case_name,
                        "docket": docket,
                        "status": "Published",
                        "url": url,
                        "citation": citation,
                        "judges": judges,
                    }
                )
        if not self.test_mode_enabled():
            self.webdriver.quit()

    def get_case_name(self, pg) -> str:
        """Get case name from page content

        :param pg: Page Element
        :return: Cleaned case name
        """
        start = False
        content = []
        for element in pg.xpath(".//*"):
            if (
                b"markedContent" in tostring(element)
                or element.text_content() == ""
            ):
                continue
            # This denotes a bolded field e.g. Respondent etc.
            if ":" in element.text_content():
                start = True
                continue
            # IDs an italics, e.g. en banc at the end of the name
            if b"transform: scaleX(0.8" in tostring(element):
                start = False
            if not start:
                continue

            content.append(element.text_content())
        case_name = " ".join(content[:-1]).replace(" ,", "").replace(" .", "")
        return re.sub(r"\s{2,}", " ", case_name.strip())
