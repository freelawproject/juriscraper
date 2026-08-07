# Scraper for New York Appellate Divisions 2nd Dept.
# CourtID: nyappdiv_2nd
# Court Short Name: NY
# Author: Andrei Chelaru
# Reviewer: mlr
# Date: 2014-07-04
from datetime import date

import nh3
from lxml import etree
from lxml.html import fromstring, tostring

from juriscraper.opinions.united_states.state import nyappdiv_1st


class Site(nyappdiv_1st.Site):
    first_opinion_date = date(2003, 9, 25)
    days_interval = 30
    court = "App Div, 2d Dept"

    @staticmethod
    def cleanup_content(content: bytes) -> bytes:
        """Remove hash altering timestamps to prevent duplicates

        Previously we've been more targeted about removing a href's but
        doctor will strip them out anyway so we should just clean our html
        content here.

        :param content: downloaded content `r.content`
        :return: content without hash altering elements
        """
        try:
            html_str = content.decode("utf-8")
        except UnicodeDecodeError:
            return content

        if not nh3.is_html(html_str):
            return content

        # remove <a> tags; allow <main> so we can extract the opinion;
        # fully drop nav/footer/header/script/style content (changes between
        # requests and pollutes hashes)
        clean_content_tags = {"script", "style", "nav", "footer", "header"}
        allowed = set(nh3.ALLOWED_TAGS) - clean_content_tags
        allowed.discard("a")
        allowed.add("main")

        cleaned = nh3.clean(
            html_str,
            tags=allowed,
            clean_content_tags=clean_content_tags,
        )

        tree = fromstring(cleaned)
        main = tree.xpath('//main[@id="main"]') or tree.xpath("//main")
        if main:
            new_tree = etree.Element("html")
            body = etree.SubElement(new_tree, "body")
            body.append(main[0])
            tree = new_tree

        normalized_html = tostring(tree, encoding="unicode", method="html")
        return normalized_html.encode()
