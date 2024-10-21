"""Scraper for Colorado Appeals Court
CourtID: coloctapp
Court Short Name: Colo. Ct. App.

History:
    - 2022-01-31: Updated by William E. Palin
    - 2023-01-05: Updated by William E. Palin
    - 2023-11-04: Updated by Honey K. Joule
    - 2023-11-19: Updated by William E. Palin
"""

import re

from lxml import html

from juriscraper.opinions.united_states.state import colo


class Site(colo.Site):
    api_court_code = "14024_02"
    days_interval = 15

    @staticmethod
    def cleanup_content(content: str) -> str:
        """Returned HTML may need editing for proper ingestion

        The HTML seems to change constantly, so some of these
        steps may be outdated (Check juriscraper#1198 and courtlistener#4443)

        - delete style and img tags which hold tokens
        that make the hash change everytime

        - delete classes which conflict with our bootstrap
        classes, such as .h2 and .h3

        :param content: html string
        :return: cleaned up html
        """
        tree = html.fromstring(content)
        remove_tags = ["//style", "//img"]
        remove_attributes = [
            "//*[@class]",
            # contains json like data with "ctm" key
            "//*[@data-data]",
            # contains coordinate like data
            "//*[@data-dest-detail]",
        ]
        for xpath in remove_tags:
            for element in tree.xpath(xpath):
                element.getparent().remove(element)

        for xpath in remove_attributes:
            attrib = re.search(r"[\w-]+", xpath).group(0)
            for element in tree.xpath(xpath):
                element.attrib.pop(attrib)

        return html.tostring(
            tree, pretty_print=True, encoding="unicode"
        ).encode("utf-8")
