from urllib.parse import urljoin

from lxml import etree

from juriscraper.opinions.united_states.state import wis


class Site(wis.Site):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.court_id = self.__module__
        self.base_url = "https://www.wicourts.gov/other/appeals/caopin.jsp"
        self.set_url()
        self.url = "https://www.wicourts.gov/other/appeals/caopin.jsp?docket_number=&range=Last+month&begin_date=04-01-2024&end_date=04-30-2024&fpb_beg_date=&fpb_end_date=&trial_judge_last=&party_name=&trial_county=&ca_district=&disp_code=&cite_type=&cite_page=&cite_volume=&pdcNo=&sortBy=date&Submit=Search"
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
            caption = caption.text_content()
            lower_court = f"Wisconsin Circuit Court, {county.text} County"
            if "[Decision/Opinion withdrawn" in caption:
                continue
            name = caption.split("[")[0].strip().replace("Errata: ", "")
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
