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

            # In juvenile cases - the case name contains the docket number
            # So we use a negative lookbehind to ignore docket numbers after
            # the word juvenile.
            regex = r"(?<!JUVENILE )((\b)(\w+-)?[\d]{2,4}-\d+)\/?"
            dockets = re.findall(regex, case["documentName"])
            docket = ", ".join([docket[0] for docket in dockets])

            # Get name by removing docket number from document text
            rgx = r"(?<!JUVENILE )((\b)(\w+-)?[\d]{2,4}-\d+)\/?,? &? ?(and)? ?"
            name = re.sub(rgx, "", case["documentName"])
            # Strip out the bad pattern with slashes between adjoined docket numbers
            name = re.sub(r"^\d+\/", "", name)

            self.cases.append(
                {
                    "name": name,
                    "docket": docket,
                    "date": date,
                    "url": urls[0],
                }
            )
