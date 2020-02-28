"""
History:
 - 2014-08-05: Adapted scraper to have year-based URLs.
"""

from juriscraper.OpinionSiteLinear import OpinionSiteLinear


class Site(OpinionSiteLinear):
    def __init__(self, *args, **kwargs):
        super(Site, self).__init__(*args, **kwargs)
        self.court_id = self.__module__
        self.url = (
            "https://www.courts.oregon.gov/publications/sc/Pages/default.aspx"
        )
        self.cases = []
        self.status = "Published"

    def _process_html(self):
        for header in self.html.xpath("//h4//a/parent::h4"):
            date_string = header.text_content().strip()
            if not date_string:
                continue
            ul = header.xpath("./following-sibling::ul")[0]
            for item in ul.xpath(".//li"):
                # Ensure two links are present (skip Petitions for Review rows)
                # see or_example_2.html
                anchors = item.xpath(".//a")
                if not (len(anchors) > 1):
                    continue
                text = item.text_content().strip()
                url = anchors[0].xpath("./@href")[0]
                docket = anchors[1].text_content().strip()
                name = text.split(")", 1)[-1]
                self.cases.append(
                    {
                        "date": date_string,
                        "name": name,
                        "docket": docket,
                        "url": url,
                    }
                )
