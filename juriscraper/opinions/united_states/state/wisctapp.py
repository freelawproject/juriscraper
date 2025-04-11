from urllib.parse import urljoin

from juriscraper.AbstractSite import logger
from juriscraper.opinions.united_states.state import wis


class Site(wis.Site):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.court_id = self.__module__
        self.base_url = "https://www.wicourts.gov/other/appeals/caopin.jsp"
        self.set_url()
        self.cite_regex = r"20\d{2}\sWI App\s\d+"

    def combine_opinions(self, url: str, docket_number: str) -> bool:
        """Combine duplicate opinions in self.cases

        Wisconsin Court of Appeals generates a row for every docket number
        for combined cases.  If this is the case and the opinions all
        point to the same document, combine the docket numbers

        :return: True if opinion already in self.cases
        """
        for case in self.cases:
            if case["url"] == url:
                case["docket"] = f"{case['docket']}, {docket_number}"
                case["docket"] = ", ".join(sorted(case["docket"].split(", ")))
                return True
        return False

    def _process_html(self):
        """Process Wisconsin Ct of Appeals rows

        :return: None
        """
        for row in self.html.xpath(".//table/tbody/tr"):
            date, docket, caption, district, county, link = row.xpath("./td")
            long_caption = caption.text_content()
            if "[Decision/Opinion withdrawn" in long_caption:
                logger.debug("Skipping withdrawn opinion: %s", long_caption)
                continue

            captions = caption.xpath(".//text()")
            if "Errata" in captions[0]:
                status, name = "Errata", captions[1]
            elif "Recommended for Publication" in captions[-1]:
                status, name = "Published", captions[0]
            else:
                status, name = "Unpublished", captions[0]

            url = urljoin(
                "https://www.wicourts.gov", link.xpath("./input")[0].name
            )
            docket_number = docket.text
            if self.combine_opinions(url, docket_number):
                logger.debug("Duplicate row: %s", name)
                continue
            lower_court = f"Wisconsin Circuit Court, {county.text} County"

            self.cases.append(
                {
                    "date": date.text,
                    "name": name.strip(),
                    "url": url,
                    "docket": docket_number,
                    "status": status,
                    "lower_court": lower_court,
                }
            )
