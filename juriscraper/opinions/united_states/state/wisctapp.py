from urllib.parse import urljoin

from lxml import etree

from juriscraper.AbstractSite import logger
from juriscraper.opinions.united_states.state import wis


class Site(wis.Site):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.court_id = self.__module__
        self.base_url = "https://www.wicourts.gov/other/appeals/caopin.jsp"
        self.set_url()
        self.cite_regex = (
            r"(?P<volume>20\d{2})\s(?P<reporter>WI App)\s(?P<page>\d+)"
        )

    @staticmethod
    def set_status(caption: etree._Element) -> str:
        """Set status of opinions

        Published opinions are either identified as marked for publication
        or if they are older opinions with Final publication date ... etc

        :param caption: The case name field
        :return:Status
        """
        full_string = caption.text_content()
        if "publication" in full_string.lower():
            status = "Published"
        elif "errata" in full_string.lower():
            status = "Errata"
        else:
            status = "Unpublished"
        return status

    def _process_html(self):
        for row in self.html.xpath(".//table/tbody/tr"):
            date, docket, caption, district, county, link = row.xpath("./td")
            caption_str = caption.text_content()
            lower_court = f"Wisconsin Circuit Court, {county.text} County"
            if "[Decision/Opinion withdrawn" in caption_str:
                logger.debug("Skipping withdrawn opinion: %s", caption_str)
                continue
            name = caption_str.split("[")[0].strip().replace("Errata: ", "")
            self.cases.append(
                {
                    "date": date.text,
                    "name": name,
                    "url": urljoin(
                        "https://www.wicourts.gov",
                        link.xpath("./input")[0].name,
                    ),
                    "docket": docket.text,
                    "status": self.set_status(caption),
                    "lower_court": lower_court,
                }
            )
