# Scraper for Supreme Court of Oklahoma
# CourtID: okla
# Court Short Name: OK
# Court Contact: webmaster@oscn.net
# Author: Andrei Chelaru
# Reviewer: mlr
# Date: 2014-07-05


from lxml import html

from juriscraper.AbstractSite import logger
from juriscraper.lib.html_utils import strip_bad_html_tags_insecure
from juriscraper.OpinionSiteLinear import OpinionSiteLinear


class Site(OpinionSiteLinear):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.court_id = self.__module__
        self.url = "https://www.oscn.net/decisions/ok/30"
        self.status = "Published"
        self.expected_content_types = ["text/html"]

    def _process_html(self):
        for row in self.html.xpath(".//li[@class='decision']"):
            name, citation = row.xpath(".//a/text()")
            url = row.xpath(".//a/@href")[0]
            date_filed_raw = row.xpath(".//span[@class='decidedDate']/text()")
            summary = row.xpath(".//p[@class='summaryParagraph']/text()")[0]

            docket = row.xpath(".//span[@class='caseNumber']/text()")
            if not docket:
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

    @staticmethod
    def cleanup_content(content):
        """Remove non-opinion HTML

        Oklahoma uses ISO-8859-1 formatting which we need to account for
        so we dont end up with ugly HTML.  Also we should remove a few sections
        and all of the A tags to avoid hyperlinking to nowhere.

        Make sure to wrap the content in an HTML tag so it can be properly
        processed on CL.

        :param content: The scraped HTML
        :return: Cleaner HTML
        """
        content = content.decode("ISO-8859-1")
        tree = strip_bad_html_tags_insecure(content, remove_scripts=True)
        for removal_class in ["tmp-citationizer", "footer", "published-info"]:
            for element in tree.xpath(f"//div[@class='{removal_class}']"):
                parent = element.getparent()
                if parent is not None:
                    parent.remove(element)
        # Remove the a tags so we dont link around to broken places
        for a_tag in tree.xpath("//a"):
            span = html.Element("span")
            span.text = a_tag.text
            a_tag.getparent().replace(a_tag, span)

        opinions_navigation = tree.xpath("//div[@id='opinons-navigation']")
        if opinions_navigation:
            opinions_navigation = opinions_navigation[0]
            parent = opinions_navigation.getparent()

            # Remove all preceding siblings
            for sibling in opinions_navigation.itersiblings(preceding=True):
                parent.remove(sibling)
            opinions_navigation.getparent().remove(opinions_navigation)

        # Find the core element with id 'oscn-content'
        core_element = tree.xpath("//*[@id='oscn-content']")[0]
        html_content = html.tostring(core_element).decode("ISO-8859-1").strip()
        return f"<html>{html_content}</html>"
