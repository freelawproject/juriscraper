from urllib.parse import urlparse

from juriscraper.AbstractSite import logger
from juriscraper.lib.string_utils import convert_date_string, titlecase
from juriscraper.OpinionSiteLinear import OpinionSiteLinear


class Site(OpinionSiteLinear):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.url = "https://cafc.uscourts.gov/category/opinion-order/feed/"
        self.court_id = self.__module__

    def _process_html(self):
        """Process HTML
        Iterate over each item in the RSS feed

        Return: None
        """
        for item in self.html.xpath("//item"):
            # Expected <title> content:
            # <title>21-1358: LEVARIO v. MCDONOUGH [OPINION], Nonprecedential</title>
            title = item.xpath("./title/text()")[0]
            # Expected <content:encoded> content:
            # <content:encoded><![CDATA[<p>Opinions/Orders posted: </p><p><a href="/opinions-orders/21-1358.opinion.10-12-2021_1847104.pdf">LEVARIO v. MCDONOUGH [OPINION](pdf)</a> <br />Appeal Number: 21-1358 <br />Origin: CAVC <br />Nonprecedential </p><p>To see more opinions and orders, follow this link: <a href="/home/case-information/opinions-orders/">Opinions and Orders</a>.</p>]]></content:encoded>
            p_element = item.xpath(
                "./encoded",
                namespaces={
                    "content": "http://purl.org/rss/1.0/modules/content/"
                },
            )[0]
            urls_raw = p_element.xpath("./p/a/@href")
            for url_raw in urls_raw:
                parsed = urlparse(url_raw)
                if parsed.path.lower().endswith(".pdf"):
                    url = url_raw
                    break
            # Expected <pubDate> content:
            # <pubDate>Tue, 12 Oct 2021 15:00:23 +0000</pubDate>
            pubdate = item.xpath("./pubdate/text()")[0]

            docket = title.split(":")[0].strip()
            title = title.split(":")[1].strip()
            name = titlecase(title.split("[")[0].strip())
            status_raw = title.split("],")[1].strip()
            status_raw = status_raw.lower()
            if "nonprecedential" in status_raw:
                status = "Unpublished"
            elif "precedential" in status_raw:
                status = "Published"
            else:
                status = "Unknown"

            self.cases.append(
                {
                    "date": pubdate,
                    "docket": docket,
                    "url": url,
                    "name": name,
                    "status": status,
                }
            )
