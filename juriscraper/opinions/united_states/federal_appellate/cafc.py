from juriscraper.lib.string_utils import titlecase
from juriscraper.OpinionSiteLinear import OpinionSiteLinear


class Site(OpinionSiteLinear):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.url = "https://cafc.uscourts.gov/category/opinion-order/feed/"
        self.court_id = self.__module__

    def _process_html(self) -> None:
        """Process the RSS feed.

        Iterate over each item in the RSS feed to extract out
        the date, case name, docket number, and status and pdf URL.
        Return: None
        """
        for item in self.html.xpath("//item"):
            title = item.xpath("./title/text()")[0]
            p_element = item.xpath(
                "./encoded",
                namespaces={
                    "content": "http://purl.org/rss/1.0/modules/content/"
                },
            )[0]

            # Check for the existence of a link to the PDF, otherwise skip.
            urls = p_element.xpath("//a[contains(@href, '.pdf')]/@href")
            if not urls:
                continue

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
                    "url": urls[0],
                    "name": name,
                    "status": status,
                }
            )
