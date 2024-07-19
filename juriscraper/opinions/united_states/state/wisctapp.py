from lxml import etree

from juriscraper.opinions.united_states.state import wis


class Site(wis.Site):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.court_id = self.__module__
        self.base_url = "https://www.wicourts.gov/other/appeals/caopin.jsp"
        self.set_url()
        # # 2024 WI App 36
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
        notes = caption.xpath("./strong/text()")
        if notes and "publication" in notes[0]:
            status = "Published"
        else:
            status = "Unpublished"
        return status

    def _process_html(self):
        for row in self.html.xpath(".//table/tbody/tr"):
            date, docket, caption, district, county, link = row.xpath("./td")
            self.cases.append(
                {
                    "date": date.text,
                    "name": caption.text,
                    "url": "https://www.wicourts.gov"
                    + link.xpath("./input")[0].name,
                    "docket": docket.text,
                    "status": self.set_status(caption),
                }
            )
