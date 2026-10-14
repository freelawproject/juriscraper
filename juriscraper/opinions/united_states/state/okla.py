# Scraper for Supreme Court of Oklahoma
# CourtID: okla
# Court Short Name: OK
# Court Contact: webmaster@oscn.net
# Author: Andrei Chelaru
# Reviewer: mlr
# Date: 2014-07-05


from lxml import html
from lxml.html import HtmlElement
from typing_extensions import Unpack, override

from juriscraper.AbstractSite import SiteOptions, logger
from juriscraper.lib.html_utils import strip_bad_html_tags_insecure
from juriscraper.lib.string_utils import CaseNameTweaker
from juriscraper.OpinionSiteLinear import OpinionSiteLinear


class Site(OpinionSiteLinear):
    def __init__(
        self,
        cnt: CaseNameTweaker | None = None,
        user_agent: str = "Juriscraper",
        **kwargs: Unpack[SiteOptions],
    ) -> None:
        super().__init__(cnt, user_agent, **kwargs)
        self.court_id = self.__module__
        self.url = "https://www.oscn.net/decisions/ok/30"
        self.status = "Published"
        self.expected_content_types = ["text/html"]
        self.should_have_results = True

    @override
    def _process_html(self) -> None:
        if not isinstance(self.html, HtmlElement):
            raise ValueError(
                "An HTML document must be downloaded before parsing."
            )
        for row in self.html.findall(".//li[@class='decision']"):
            name, citation = row.xpath(".//a/text()")
            url: str = row.xpath(".//a/@href")[0]
            date_filed_raw: list[str] = row.xpath(
                ".//span[@class='decidedDate']/text()"
            )
            summary: str = row.xpath(".//p[@class='summaryParagraph']/text()")[
                0
            ]

            docket: list[str] = row.xpath(
                ".//span[@class='caseNumber']/text()"
            )
            if not bool(docket):
                logger.debug("Skipping row without docket number")
                continue
            docket_number_raw = docket[0].strip()

            self.cases.append(
                {
                    "date": date_filed_raw[0].strip().split()[1],
                    "name": name,
                    "docket": docket_number_raw.split()[1],
                    "citation": citation,
                    "url": url,
                    "summary": summary.strip(),
                }
            )

    @override
    @staticmethod
    def cleanup_content(content: bytes) -> bytes:
        """Remove non-opinion HTML

        Oklahoma uses ISO-8859-1 formatting which we need to account for
        so we dont end up with ugly HTML.  Also we should remove a few sections
        and all of the A tags to avoid hyperlinking to nowhere.

        Make sure to wrap the content in an HTML tag so it can be properly
        processed on CL.

        :param content: The scraped HTML
        :return: Cleaner HTML
        """
        text = content.decode("ISO-8859-1")
        tree = strip_bad_html_tags_insecure(text, remove_scripts=True)

        # Remove unwanted elements using CSS selectors
        selectors_to_remove = [
            ".tmp-citationizer",
            ".footer",
            "footer",
            ".published-info",
            "#opinons-navigation",  # old versions typo
            "#opinions-navigation",
        ]

        for selector in selectors_to_remove:
            for element in tree.cssselect(selector):
                parent = element.getparent()
                if parent is not None:
                    parent.remove(element)

        # Remove the a tags so we dont link around to broken places
        # Remove the <a> tags so we don't link around to broken places
        a_tags: list[HtmlElement] = tree.xpath("//a")
        for a_tag in a_tags:
            span = html.Element("span")
            span.text = a_tag.text
            parent = a_tag.getparent()
            if parent is not None:
                parent.replace(a_tag, span)

        navigation_elements: list[HtmlElement] = tree.xpath(
            "//div[@id='opinons-navigation']"
        )
        if bool(navigation_elements):
            opinions_navigation = navigation_elements[0]
            parent = opinions_navigation.getparent()

            # Remove all preceding siblings
            if parent is not None:
                for sibling in opinions_navigation.itersiblings(
                    preceding=True
                ):
                    parent.remove(sibling)
                parent.remove(opinions_navigation)

        # remove comments that generate duplicates
        comments = tree.xpath("//comment()")
        for comment in comments:
            if comment.getparent():
                comment.getparent().remove(comment)

        # Find the core element with id 'oscn-content'
        core_element: HtmlElement = tree.xpath("//*[@id='oscn-content']")[0]
        html_content = html.tostring(core_element).decode("ISO-8859-1").strip()
        return f"<html>{html_content}</html>".encode("ISO-8859-1")
