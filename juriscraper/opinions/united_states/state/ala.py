import re
from pprint import pprint

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
        self.initiate_webdriven_session()
        self.html = fromstring(self.webdriver.page_source)

        for a in self.html.xpath('//*[@id="FileTable"]/tbody/tr/td/a')[:5]:
            self.webdriver.get(a.get("href"))
            print(a.get("href"))
            self.webdriver.implicitly_wait(10000)

            page_content = self.find_element_by_id("viewer").text

            html = fromstring(self.webdriver.page_source)

            for link in html.xpath(".//section/a/@href"):
                title = html.xpath(f"//a[@title='{link}']/@id")
                if not title:
                    continue
                title_id = title[0]
                appellate_court = html.xpath(
                    f"//span[@aria-owns='{title_id}']/text()"
                )
                case_info = []
                author = None
                date_filed = re.findall(
                    r"(JANUARY|FEBRUARY|MARCH|APRIL|MAY|JUNE|JULY|AUGUST|SEPTEMBER|OCTOBER|NOVEMBER|DECEMBER \d{1,2}, \d{4})",
                    page_content,
                )[0]
                page_content = re.sub(r"\n-\n", "-", page_content)
                page_content = re.sub("\n ", " ", page_content)
                docket = ""
                for row in page_content.splitlines():
                    m = re.findall(r"((\d{4}-\d{4})|(\d{7}) )", row)
                    if m:
                        docket = list({x for x in m[0] if x})[0]
                        case_info = []
                        case_info.append(row)
                    if "JUSTICE" in row:
                        author = row
                    if case_info:
                        case_info.append(row)
                    if row == appellate_court[0]:
                        break
                case_data = " ".join(case_info)
                case_title = case_data.split(docket)[1].strip()
                self.cases.append(
                    {
                        "date": date_filed,
                        "name": case_title,
                        "docket": docket,
                        "status": "Published",
                        "url": link,
                        "author": author,
                    }
                )
        pprint(self.cases)
        self.webdriver.quit()
