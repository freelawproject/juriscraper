"""
Scraper for Alabama Supreme Court
CourtID: ala
Court Short Name: Alabama
Author: William Palin
Court Contact:
History:
 - 2023-01-04: Created.
Notes:
 - This may be the only court (with the app. cts) that requires selenium
"""

import re

from lxml.html import fromstring, tostring

from juriscraper.OpinionSiteLinearWebDriven import OpinionSiteLinearWebDriven


class Site(OpinionSiteLinearWebDriven):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.court_id = self.__module__
        self.url = (
            "https://judicial.alabama.gov/decision/supremecourtdecisions"
        )
        self.uses_selenium = True

    def _process_html(self):
        if not self.test_mode_enabled():
            self.initiate_webdriven_session()

        # Fetch from the last four Released documents
        if not self.test_mode_enabled():
            links = self.html.xpath('//*[@id="FileTable"]/tbody/tr/td/a')[:4]
        else:
            links = ["fake_link"]
        for link in links:
            if not self.test_mode_enabled():
                # Fetch the PDF at the a_href link in the file table and parse it
                self.webdriver.get(link.get("href"))
                date_filed = link.text_content().split("day, ")[1].strip()
                # Wait for pdf to render
                self.webdriver.implicitly_wait(10000)
                # And click next twice to make sure we fully render the PDF content
                self.find_element_by_id("next").click()
                self.find_element_by_id("next").click()

                # Set the content for lxml parsing after this rendering.
                self.html = fromstring(self.webdriver.page_source)
            else:
                super()._download()
                date_filed = "JANUARY 4, 2023"

            # Iterate over the elements to extract out the content
            start = False
            content = []
            author = ""
            for element in self.html.xpath("//*"):
                if b"markedContent" in tostring(element):
                    continue
                elif b"left: 120" in tostring(
                    element
                ) or b"left: 119" in tostring(element):
                    # Add an author if available
                    if (
                        b"JUDGE" in tostring(element)
                        or b"JUSTICE" in tostring(element)
                        or b"PER CURIAM" in tostring(element)
                    ):
                        author = element.text_content()
                    if b"REHEARING" in tostring(element):
                        author = ""
                    start = True
                    content = []
                    content.append(element.text_content())

                elif start and b"aria-owns" in tostring(element):
                    # Ascertain URL
                    ao = element.get("aria-owns")
                    if not ao:
                        start = False
                        continue
                    if len(ao.split()) == 1:
                        urls = self.html.xpath(f".//a[@id='{ao}']/@href")
                    else:
                        urls = self.html.xpath(
                            f".//a[@id='{ao.split()[0]}']/@href"
                        )
                    # Cleanup whitespace and identify docket and case title
                    content.append(element.text_content())
                    all_content = " ".join(content)
                    cleaned_content = re.sub(r"\s{2,}", " ", all_content)
                    docket = re.findall(r"^[\w-]*", cleaned_content)[0]
                    title = (
                        cleaned_content.split("(")[0]
                        .replace(docket, "")
                        .strip()
                    )
                    content = []
                    start = False
                    # Add case and start over
                    self.cases.append(
                        {
                            "date": date_filed,
                            "name": title,
                            "docket": docket,
                            "status": "Published",
                            "url": urls[0],
                            "author": author,
                        }
                    )
                elif start:
                    content.append(element.text_content())
        if not self.test_mode_enabled():
            self.webdriver.quit()
