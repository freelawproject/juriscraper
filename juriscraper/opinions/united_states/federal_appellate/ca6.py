"""
CourtID:	ca6
Court Contact:	WebSupport@ca6.uscourts.gov
"""

from urllib.parse import urljoin

from juriscraper.AbstractSite import logger
from juriscraper.OpinionSiteLinear import OpinionSiteLinear


class Site(OpinionSiteLinear):
    initials_to_judges = {
        # See https://www.ca6.uscourts.gov/judges
        # Commented is their "Comission date"
        "RBG": "Ralph B. Guy, Jr.",  # October 17, 1985
        "DJB": "Danny J. Boggs",  # March 25, 1986
        "AEN": "Alan E. Norris",  # July 1, 1986
        "RFS": "Richard F. Suhrheinrich",  # July 10, 1990
        "EES": "Eugene E. Siler, Jr.",  # September 16, 1991
        "AMB": "Alice M. Batchelder",  # December 2, 1991
        "MCD": "Martha Craig Daughtrey",  # November 22, 1993
        "KNM": "Karen Nelson Moore",  # March 24, 1995
        "RGC": "R. Guy Cole, Jr.",  # December 26, 1995
        "ELC": "Eric L. Clay",  # August 1, 1997
        "RLG": "Ronald Lee Gilman",  # November 7, 1997
        "JSG": "Julia Smith Gibbons",  # July 31, 2002
        "JMR": "John M. Rogers",  # November 26, 2002
        "JSS": "Jeffrey S. Sutton",  # May 5, 2003
        "DLC": "Deborah L. Cook",  # May 7, 2003
        "DWM": "David W. McKeague",  # June 10, 2005
        "RAG": "Richard Allen Griffin",  # June 10, 2005
        "RMK": "Raymond M. Kethledge",  # July 7, 2008
        "HNW": "Helene N. White",  # August 8, 2008
        "JBS": "Jane Branstetter Stranch",  # September 15, 2010
        "ART": "Amul R. Thapar",  # May 25, 2017
        "JKB": "John K. Bush",  # July 21, 2017
        "JLL": "Joan L. Larsen",  # November 2, 2017
        "JBN": "John B. Nalbandian",  # May 17, 2018
        "CAR": "Chad A. Readler",  # March 7, 2019
        "EEM": "Eric E. Murphy",  # March 11, 2019
        "SDD": "Stephanie Dawkins Davis",  # June 14, 2022
        "ABM": "Andre B. Mathis",  # September 27, 2022
        "RSB": "Rachel S. Bloomekatz",  # July 20, 2023
        "KGR": "Kevin G. Ritz",  # September 19, 2024
        "WDH": "Whitney D. Hermandorfer",  # July 17, 2025
    }
    bap_scraper = False

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.court_id = self.__module__
        self.url = "http://www.opn.ca6.uscourts.gov/opinions/opinions.php"
        self.should_have_results = True

    def _process_html(self):
        for row in self.html.xpath("//table/tr[not(th)]"):
            filename = row.xpath("td[1]/a/text()")[0].lower()
            lower_court = row.xpath("td[4]/font/text()")[0]

            # other entities that appeal to `ca6`: FCC, BIA
            if "District" in lower_court:
                lower_court = (
                    f"United States District Court for the {lower_court}"
                )

            is_bap_opinion = (
                "b" in filename or "bankruptcy court" in lower_court.lower()
            )

            if is_bap_opinion:
                if not self.bap_scraper:
                    logger.info("Skipping `bap6` opinion %s", filename)
                    continue
            else:
                if self.bap_scraper:
                    logger.info("Skipping `ca6` opinion %s", filename)
                    continue

            if "n" in filename:
                status = "Unpublished"
            elif "p" in filename:
                status = "Published"
            else:
                status = "Unknown"

            panel_initials = row.xpath("td[5]/text()")[0]

            self.cases.append(
                {
                    "url": urljoin(self.url, row.xpath("td[1]/a/@href")[0]),
                    "docket": row.xpath("string(td[2])").strip(),
                    "date": row.xpath("td[3]/text()")[0],
                    "name": row.xpath("td[4]/text()")[0],
                    "lower_court": lower_court,
                    "judge": self.parse_judges(panel_initials),
                    "status": status,
                }
            )

    def parse_judges(self, initials: str) -> str:
        """Parse judge initials into full names

        :param initials: comma separated 3 letter initials
        :return: colon separated full judge names
        """
        judges = ""

        for initial in initials.split(","):
            judge = self.initials_to_judges.get(initial.strip())
            if not judge:
                logger.info("No judge name for initial %s", initial)
            else:
                judges += f"{judge}; "

        return judges.strip("; ")
