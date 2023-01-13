# Scraper for Kansas Appeals Court
# CourtID: kanctapp_u

from juriscraper.OpinionSiteLinear import OpinionSiteLinear


class Site(OpinionSiteLinear):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.court_id = self.__module__
        self.url = "https://www.kscourts.org/cases-opinions/opinions.html"

    def _process_html(self):
        url = None
        status = None
        cap_column = self.html.xpath('//h2[@id="kc-cap"]')[0].getparent()
        for element in cap_column.xpath(".//*"):
            if element.tag == "h2":
                if element.attrib["id"] == "kc-cau":
                    status = "Unpublished"
            elif element.tag == "h3" and status:
                date = element.text_content()[6:]
            elif element.tag == "p" and status:
                case_content = element.text_content()
                if "None Released" in case_content:
                    continue
                components = case_content.split(" - ")
                url = element.xpath(".//a/@href")[0]
            if url == None:
                continue
            if not status:
                continue
            self.cases.append(
                {
                    "status": status,
                    "date": date,
                    "docket": components[0],
                    "name": components[1],
                    "url": url,
                }
            )
            url = None
