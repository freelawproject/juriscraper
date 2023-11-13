# Scraper for Minnesota Supreme Court
# CourtID: minn
# Court Short Name: MN
# Author: Andrei Chelaru
# Reviewer: mlr
# Date: 2014-07-03
# Contact:  Liz Reppe (Liz.Reppe@courts.state.mn.us), Jay Achenbach (jay.achenbach@state.mn.us)
import re

from juriscraper.OpinionSiteLinear import OpinionSiteLinear

# Need to contact the court, but they have a captcha on the pages that make this
# a rather unqiue scraper. I found that if i first go to the a differnet
# state website - even if the captcha triggers on that url i can still access the
# search query.


class Site(OpinionSiteLinear):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.court_id = self.__module__
        self.parameters = {
            "v:sources": "mn-law-library-opinions",
            "query": f" (url:/archive/supct) ",
            "sortby": "date",
        }
        self.url = "http://minnesota.gov/"
        self.search_url = "https://mn.gov/law-library/search/#"
        self.headers = {
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Sec-Fetch-Site": "same-origin",
            "Sec-Fetch-Dest": "document",
            "Accept-Language": "en-US,en;q=0.9",
            "Sec-Fetch-Mode": "navigate",
            "Host": "mn.gov",
            "User-Agent": "Juriscraper/3.0 Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15",
            "Referer": "https://mn.gov/law-library/search/?v%3Asources=mn-law-library-opinions&query=+%28url%3A%2Farchive%2Fsupct%29+&citation=&qt=&sortby=&docket=&case=&v=&p=&start-date=&end-date=",
            # 'Accept-Encoding': 'gzip, deflate, br',
            "Connection": "keep-alive",
        }
        self.status = "Published"

    def _request_url_get(self, url):
        """Execute GET request and assign appropriate request dictionary
        values
        """
        self.request["session"].get(self.url, headers=self.headers, timeout=30)
        self.request["response"] = self.request["session"].get(
            self.search_url,
            params=self.parameters,
            headers=self.headers,
            timeout=30,
        )

    def _process_html(self) -> None:
        """Process the html and extract out the opinions

        :return: None
        """
        for case in self.html.xpath("//div[@class='searchresult']"):
            url = case.xpath(".//a/@href")[0]
            name = case.xpath(".//a/text()")[0]
            m = re.match(r"(.*)\. A2[23]", name)
            if m:
                name = m.groups()[0]

            summary = case.xpath(
                ".//div[@class='searchresult_snippet']/text()"
            )[0]
            raw_date = case.xpath(".//div[@class='searchresult_date']")[
                -1
            ].text_content()
            date = re.sub(r"\s+", " ", raw_date).split(":")[1].strip()
            docket = url.split("/")[-1].split("-")[0][2:]
            self.cases.append(
                {
                    "date": date,
                    "name": name,
                    "url": f"http:{url}",
                    "summary": summary,
                    "docket": docket,
                }
            )
