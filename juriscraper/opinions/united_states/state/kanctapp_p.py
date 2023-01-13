# Scraper for Kansas Appeals Court
# CourtID: kanctapp

from juriscraper.OpinionSiteLinear import OpinionSiteLinear


class Site(OpinionSiteLinear):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.court_id = self.__module__
        self.url = "https://www.kscourts.org/cases-opinions/opinions.html"

    def _process_html(self):
        url = None
        cap_column = self.html.xpath('//h2[@id="kc-cap"]')[0].getparent()
        for element in cap_column.xpath(".//*"):
            if element.tag == "h2":
                if element.attrib["id"] == "kc-cap":
                    status = "Published"
                elif element.attrib["id"] == "kc-cau":
                    status = "Unpublished"
                    break
            elif element.tag == "h3":
                date = element.text_content()[6:]
            elif element.tag == "p":
                case_content = element.text_content()
                components = case_content.split(" - ")
                if "None Released" in case_content:
                    continue
                url = element.xpath(".//a/@href")[0]
            if url == None:
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
