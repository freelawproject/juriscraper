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

from lxml.html import fromstring

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
                left = element.xpath(
                    'substring-before(substring-after(@style, "left: "), "px")'
                )
                if element.cssselect("span[class='markedContent']"):
                    continue
                elif left and round(float(left)) == 120:
                    start = True
                    content = []
                    content.append(element.text_content())

                    text = element.text_content()
                    if (
                        "JUDGE" in text
                        or "JUSTICE" in text
                        or "PER CURIAM" in text
                    ):
                        author = text
                    if "REHEARING" in text:
                        author = ""

                elif start and element.cssselect("span[aria-owns]"):
                    ao = element.get("aria-owns")
                    if not ao:
                        start = False
                        continue
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
                            "judge": author,
                        }
                    )
                elif start:
                    content.append(element.text_content())
        if not self.test_mode_enabled():
            self.webdriver.quit()
