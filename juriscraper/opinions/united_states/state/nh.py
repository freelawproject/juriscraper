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
    - 2021-12-29: Updated for new web site, by flooie and satsuki-chan
Notes:
    To filer documents per year, the API expects the key number for the year
    in parameter:
    - 'tag': for years 2019 to date
        * 2021: tag=1206    * 2020: tag=1366    * 2019: tag=1416
    - 'subcategory': for years 2009 to 2018
        * 2018: subcategory=1601    * 2017: subcategory=1596
        * 2016: subcategory=1591    * 2015: subcategory=1586
        * 2014: subcategory=1581    * 2013: subcategory=1576
        * 2012: subcategory=1571    * 2011: subcategory=1566
        * 2010: subcategory=1561    * 2009: subcategory=1556
    Only one parameter can have a key number; using both with a value in the
    same request (even with a valid key) returns zero documents.
    Using none, returns all documents (regardless of the publication year)
    found with the other parameters values.
    For this scraper, filtering documents per year is not necesary.
    Examples:
        - https://www.courts.nh.gov/content/api/documents?text=&category=+undefined&purpose=1331+undefined&tag=+&subcategory=1556&sort=field_date_posted|desc&page=3&size=10
        - https://www.courts.nh.gov/content/api/documents?text=&category=+undefined&purpose=1331+undefined&tag=1366+&subcategory=&sort=field_date_posted|desc&page=1&size=25
"""

import re
from typing import Tuple

from lxml.html import fromstring

from juriscraper.AbstractSite import logger
from juriscraper.OpinionSiteLinear import OpinionSiteLinear


class Site(OpinionSiteLinear):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.court_id = self.__module__
        # Parameters are included in the URL because this court's API only
        # allows GET requests. Current architecture for scrapers only includes
        # parameters in requests with the POST method
        self.url = "https://www.courts.nh.gov/content/api/documents?sort=field_date_posted%7Cdesc&page=1&size=30&purpose=1331"
        self.status = "Published"

    def _process_html(self) -> None:
        for case in self.html["data"]:
            content = fromstring(case["documentContent"])
            urls = content.xpath(
                ".//div[@class='document__detail__title']//a/@href"
            )
            if not urls:
                logger.info(f"Opinion without URL to file: {case}")
                continue

            date = case["documentPosted"]
            if not date:
                logger.info(f"Opinion without date: {case}")
                continue

            name, docket = self.name_docket(case["documentName"])
            self.cases.append(
                {
                    "name": name,
                    "docket": docket,
                    "date": date,
                    "url": urls[0],
                }
            )

    def name_docket(self, title) -> Tuple[str, str]:
        """
        Expected title values:
            - 2020-0544 and 2020-0554, In re G.B.
            - 2020-0528, 2020-0546, 2020-0548, In re S.A. & a.
            - 2019-0283 In re R.M.
            - 2017-0336 & 2019-0071  State of New Hampshire v. Daniel Turcotte
            - 2014-0315, Deere & Company & a. v. The State of New Hampshire 2014-0441, Kubota Tractor Corporation v. The State of New Hampshire 2014-0575, Husqvarna Professional Products, Inc. v. The State of New Hampshire
            - 2013-0779, Ichiban Japanese Steakhouse, Inc. v. Kymberly Rocheleau, and 2013-0780, Ichiban Japanese Steakhouse, Inc. v. Samantha Greaney
            - 2013-0513, Greg DuPont v. Nashua Police Department (consolidated with 2014-0017, Gregory DuPont v. Peter McDonough & a.)
            - 2013-0403, 2013-0445, and 2013-0593, In re Guardianship of Madelyn B.
            - 2013-0392. State of New Hampshire v. Kevin Balch
            - 010-290  Eric Lee Knight v. Cheryl Ann Maher
            - 2010-233/2010-234 Appeal of the Hartford Insurance Company (New Hampshire Compensation Appeals Board)
            - 10-436, New Hampshire Health Care Association & a. v. Governor & a.
            - ADM-2009-024, Application of G.W.
            - 2008-912, State of New Hampshire v. Charles Glenn, Jr. (modified by order dated Sept. 14, 2010)
            - 2006-329, 2006-334, I/M/O State of NH and Estate of Frank Crabtree, III; I/M/O Katherine Crabtree & a.
            - 2006-406, IN RE JUVENILE 2006-0406
            - LD-2016-0005, Petition of Sanjeev Lath & a.
            - LD-06-009, BOSSE'S CASE
        Notes:
            'and' was chosen as separator for opinions with several cases' names because the current architecture for scrapers removes semicolons from names.
        """
        docket_re = r"(?P<docket>(LD-|ADM-)?\d{2,4}-\d{2,5})"
        docket_name = re.search(
            r"(?P<docket>\d{2,4}-\d{2,5}),? (?P<name>In Re (Juvenile|Father) \d{2,4}-\d{2,5})",
            title,
            re.IGNORECASE,
        )
        if docket_name:
            docket = docket_name.group("docket")
            name = docket_name.group("name")
        else:
            dockets = re.findall(docket_re, title)
            docket = ", ".join([d[0] for d in dockets])
            name = (
                re.sub(docket_re, "| ", title).strip("| ").lstrip(" ,;.&/)|")
            )
            if name[0:3].lower() == "and":
                name = name[3:]
                name = name.lstrip(" ,;.&/)|")

            names = re.search(
                r"(?P<first_name>.+)\(?consolidated with(?P<second_name>.+)\)?",
                name,
                re.IGNORECASE,
            )
            if names:
                f_name = names.group("first_name").rstrip(" ,;(|")
                s_name = names.group("second_name").lstrip(" ,;|").rstrip(" )")
                name = f"{f_name}| {s_name}"

            names = re.search(
                r"(?P<name>.+)(\(modified.+\)|(\(|-)\s*originally issued.+\)?)",
                name,
                re.IGNORECASE,
            )
            if names:
                name = f"{names.group('name').strip()}"

            name = re.sub(
                r"(\s*(,|;|\(|\|))?\s*(and|,|;|\(|\|)\s*\|", "|", name
            )
            name = re.sub(r"\|\s*(,|;|\)|\|)(\s*(,|;|\)|\|))?", "|", name)
            name = re.sub(r"\s+\|", "|", name).rstrip(",;|")
            name = re.sub(r"\|", " and ", name)
        return name, docket
