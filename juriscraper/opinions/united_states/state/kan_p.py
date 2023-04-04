# Scraper for Kansas Appeals Court
# CourtID: kan_p

from juriscraper.OpinionSiteLinear import OpinionSiteLinear


class Site(OpinionSiteLinear):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.court_id = self.__module__
        self.url = "https://www.kscourts.org/cases-opinions/opinions.html"
        self.status = "Published" if "_p" in self.court_id else "Unpublished"
        self.xpath = "kc-scu" if "kan_" in self.court_id else "kc-cau"
        self.rows = "preceding" if "_p" in self.court_id else "following"

    def _process_html(self):
        h2_element = self.html.xpath(f'//h2[@id="{self.xpath}"]')[0]
        ul_elements = h2_element.xpath(f"{self.rows}-sibling::ul")
        for ul in ul_elements:
            if "None Released" in ul.text_content():
                continue
            date = ul.getprevious().text_content()[6:]
            for item in ul.xpath(".//p"):
                components = item.text_content().split(" - ")
                self.cases.append(
                    {
                        "status": self.status,
                        "date": date,
                        "docket": components[0],
                        "name": components[1],
                        "url": item.xpath(".//a/@href")[0],
                    }
                )
