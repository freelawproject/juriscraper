"""
Scraper for New Hampshire Supreme Court
CourtID: nh
Court Short Name: NH
Court Contact: webmaster@courts.state.nh.us
Author: Andrei Chelaru
Reviewer: mlr
History:
    - 2014-06-27: Created
    - 2014-10-17: Updated by mlr to fix regex error.
    - 2015-06-04: Updated by bwc so regex catches comma, period, or
    whitespaces as separator. Simplified by mlr to make regexes more semantic.
    - 2016-02-20: Updated by arderyp to handle strange format where multiple
    case names and docket numbers appear in anchor text for a single case pdf
    link. Multiple case names are concatenated, and docket numbers are
    concatenated with ',' delimiter
    - 2021-12-23: Updated for new web site, by flooie and satsuki-chan
"""

import re

from lxml.html import fromstring

from juriscraper.AbstractSite import logger
from juriscraper.OpinionSiteLinear import OpinionSiteLinear


class Site(OpinionSiteLinear):
    def __init__(self, *args, **kwargs):
        """
        To filer documents per year, the API expects the key number for the
        year in parameter:
        - 'tag': for years 2019 to date
            * 2021: tag=1206    * 2020: tag=1366    * 2019: tag=1416
        - 'subcategory': for years 2009 to 2018
            * 2018: subcategory=1601    * 2017: subcategory=1596
            * 2016: subcategory=1591    * 2015: subcategory=1586
            * 2014: subcategory=1581    * 2013: subcategory=1576
            * 2012: subcategory=1571    * 2011: subcategory=1566
            * 2010: subcategory=1561    * 2009: subcategory=1556
        Only one can have a key number; using both with a value in the same
        request (even with a valid key) returns zero documents.
        Using none, returns all documents found with other parameters values.
        Examples:
            - https://www.courts.nh.gov/content/api/documents?text=&category=+undefined&purpose=1331+undefined&tag=+&subcategory=1556&sort=field_date_posted|desc&page=3&size=10
            - https://www.courts.nh.gov/content/api/documents?text=&category=+undefined&purpose=1331+undefined&tag=1366+&subcategory=&sort=field_date_posted|desc&page=1&size=25
        """
        super().__init__(*args, **kwargs)
        self.court_id = self.__module__
        # Parameters are included in URL because this court's API only allows
        # GET requests. Current architecture for scrapers only includes
        # parameters in requests with the POST method
        self.url = "https://www.courts.nh.gov/content/api/documents?sort=field_date_posted%7Cdesc&page=1&size=30&purpose=1331"
        self.parameters = {
            "sort": "field_date_posted|desc",
            "page": "1",
            # Page documents size isn't limited to website defaults: 5, 10 or 25
            "size": "30",
            # Opinions have a "documentPurposes" value of "1331|"
            "purpose": "1331",
        }

    def _process_html(self) -> None:
        """
        Expected 'documentName' values:
            - 2020-0544 and 2020-0554, In re G.B.
            - 2020-0528, 2020-0546, 2020-0548, In re S.A. & a.
            - 2019-0283 In re R.M.
            - 2017-0336 & 2019-0071  State of New Hampshire v. Daniel Turcotte
            - 2013-0779, Ichiban Japanese Steakhouse, Inc. v. Kymberly Rocheleau, and 2013-0780, Ichiban Japanese Steakhouse, Inc. v. Samantha Greaney
            - 2013-0403, 2013-0445, and 2013-0593, In re Guardianship of Madelyn B.
            - 2013-0392. State of New Hampshire v. Kevin Balch
            - 010-290  Eric Lee Knight v. Cheryl Ann Maher
            - 10-436, New Hampshire Health Care Association & a. v. Governor & a.
            - 2006-329, 2006-334, I/M/O State of NH and Estate of Frank Crabtree, III; I/M/O Katherine Crabtree & a.
            - LD-2016-0005, Petition of Sanjeev Lath & a.
            - LD-06-009, BOSSE'S CASE
        """
        name_re = (
            r"(?P<docket>(((LD-|)\d{2,4}-\d{3,},\s*|)(LD-|)\d{2,4}-\d{3,}(,\s*(&|and)|\s*(&|and)|,)\s*|)(LD-|)\d{2,4}-\d{3,})"
            r"(?P<name>.*)"
        )
        name_sec_re = (
            r"(?P<name_1>.*)"
            r"(?P<docket_2>(\s*(&|and)|,)\s*(LD-|)\d{2,4}-\d{3,})"
            r"(?P<name_2>.*)"
        )
        for case in self.html["data"]:
            try:
                url = fromstring(case["documentContent"]).xpath(
                    ".//div[@class='document__detail__title']//a/@href"
                )[0]
            except:
                logger.info(f"Cannot find file for case: {case}")
                continue
            try:
                docket_name = re.search(name_re, case["documentName"])
                docket = docket_name.group("docket").strip()
                name = docket_name.group("name").strip().lstrip(",.").strip()
                docket_name_sec = re.search(name_sec_re, name)
                if docket_name_sec:
                    name_fir = (
                        docket_name_sec.group("name_1")
                        .strip()
                        .rstrip(",")
                        .strip()
                    )
                    docket_sec = (
                        docket_name_sec.group("docket_2")
                        .strip()
                        .lstrip(",")
                        .strip()
                    )
                    name_sec = (
                        docket_name_sec.group("name_2")
                        .strip()
                        .lstrip(",.")
                        .strip()
                    )
                    name = f"{name_fir} and {name_sec}"
                    docket = f"{docket}, {docket_sec}"

                dockets = (
                    docket.replace("&", " ")
                    .replace("and", " ")
                    .replace(",", " ")
                    .split()
                )
                docket = ", ".join(dockets)
            except:
                logger.warning(f"Cannot find docket and name for case: {case}")
                continue
            date = case["documentPosted"]
            self.cases.append(
                {
                    "name": name,
                    "docket": docket,
                    "date": date,
                    "status": "Published",
                    "url": url,
                }
            )
